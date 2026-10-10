"""Deterministic logic for SkinPilot.

All matching, filtering, scoring and routine rules live here as plain Python. The LLM agent only
chooses which tool to call and explains the results; it never invents products, strengths or rules.

Optional live check: ingredient lists are looked up on Open Beauty Facts (a free, community-run
database). Coverage is patchy, so a missing result means "not found", not "unsafe" or "safe".
"""
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from knowledge import (ALCOHOL_TERMS, ALIASES, CATALOG, CONCERNS, ESSENTIAL_OIL_TERMS, FRAGRANCE_TERMS,
                       GENTLE_ONLY, INGREDIENTS)

OBF_URL = "https://world.openbeautyfacts.org/cgi/search.pl"
PRODUCT_TYPES = ("cleanser", "moisturizer", "sunscreen", "treatment")
FRAGRANCE_WORDS = ("fragrance", "parfum", "perfume", "scent")


# ----------------------------------------------------------------- helpers
def _md(headers, rows):
    def fmt(v):
        return "n/a" if v is None else str(v)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(fmt(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _tf(v):
    return {True: "yes", False: "no", None: "unknown"}[v]


def avoid_terms(profile):
    return [t.strip().lower() for t in re.split(r"[,\n;]", profile.get("avoid_text", "")) if t.strip()]


def irritation_cap(profile):
    """Highest irritation level (0-3) the profile can reasonably take."""
    cap = 3
    diagnosed = set(profile.get("diagnosed", []))
    concerns = profile.get("concerns", [])
    if profile.get("skin_type") == "Sensitive" or "Redness / rosacea-like flushing" in concerns or "Rosacea" in diagnosed \
            or "Another condition diagnosed by a doctor" in diagnosed:
        cap = 2
    if "Eczema-prone / very sensitive skin" in concerns or diagnosed & GENTLE_ONLY:
        cap = 1
    return cap


def _fragrance_strict(profile):
    return any(any(w in t for w in FRAGRANCE_WORDS) for t in avoid_terms(profile))


def _sensitive_mode(profile):
    return irritation_cap(profile) <= 2 or profile.get("fragrance_sensitive", False)


def detect_current_actives(text):
    text = (text or "").lower()
    return [ing for ing, words in ALIASES.items() if any(w in text for w in words)]


# ----------------------------------------------------------------- tool 1: profile analysis
def analyze_profile(profile):
    cap = irritation_cap(profile)
    concerns = profile.get("concerns", [])
    totals = {}
    for c in concerns:
        for ing, w in CONCERNS[c]["ingredients"]:
            totals[ing] = totals.get(ing, 0) + w
    usable, held_back, excluded = [], [], []
    for ing, score in sorted(totals.items(), key=lambda x: -x[1]):
        info = INGREDIENTS[ing]
        if profile.get("pregnant") and info["pregnancy"] == "avoid":
            excluded.append((ing, "not recommended during pregnancy / breastfeeding"))
        elif info["irritation"] > cap:
            held_back.append((ing, f"irritation level {info['irritation']} is above your cap of {cap}; "
                                   "revisit with a dermatologist"))
        else:
            preg = info["pregnancy"].replace("_", " ")
            if profile.get("pregnant") and info["pregnancy"] == "ask_doctor":
                preg = "ASK YOUR DOCTOR FIRST"
            usable.append((ing, score, info["evidence"], info["strength"], info["irritation"], preg, info["notes"]))
    lines = [
        "SKIN PROFILE ANALYSIS",
        f"Skin type: {profile.get('skin_type')} | Concerns: {', '.join(concerns) or 'none given'}",
        f"Doctor-diagnosed conditions: {', '.join(profile.get('diagnosed', [])) or 'none stated'}",
        f"Pregnant / breastfeeding / trying to conceive: {'yes' if profile.get('pregnant') else 'no'}",
        f"Fragrance sensitivity: {'yes' if profile.get('fragrance_sensitive') else 'not stated'}",
        f"Ingredients/allergens to avoid (user): {', '.join(avoid_terms(profile)) or 'none stated'}",
        f"Irritation cap applied (0 = very gentle, 3 = strong actives allowed): {cap}",
        "",
        "INGREDIENT STRATEGY (higher priority score = more relevant to your concerns):",
        _md(["ingredient", "priority", "evidence", "typical strength", "irritation 0-3", "pregnancy", "notes"], usable),
    ]
    if held_back:
        lines += ["", "HELD BACK (effective but too harsh for your profile for now):",
                  _md(["ingredient", "reason"], held_back)]
    if excluded:
        lines += ["", "EXCLUDED:", _md(["ingredient", "reason"], excluded)]
    current = detect_current_actives(profile.get("current", ""))
    lines += ["", f"Current routine as written by the user: {profile.get('current') or 'not provided'}"]
    if current:
        lines.append(f"Active ingredients detected in the current routine: {', '.join(current)}. "
                     "Avoid doubling up on these; add one new active at a time.")
    lines += ["", "WHEN TO SEE A DOCTOR / DERMATOLOGIST (per concern):"]
    for c in concerns:
        lines.append(f"- {c}: {CONCERNS[c]['see_doctor']}.")
    notes = []
    if profile.get("diagnosed"):
        notes.append("The user has a doctor-diagnosed condition. Treatment is directed by their dermatologist: "
                     "products here are only supportive care (gentle cleansing, moisturising, sun protection) "
                     "and must never replace or be mixed with prescribed treatment without asking the doctor.")
    if profile.get("pregnant"):
        notes.append("Pregnancy/breastfeeding: retinoids are excluded; items marked 'ask your doctor first' "
                     "should be cleared with an obstetrician or dermatologist.")
    notes.append("General safety rules: patch-test every new product on the jawline or behind the ear for 48 hours; "
                 "introduce one new product at a time, about 2 weeks apart; stop and seek care if there is swelling, "
                 "blistering, severe burning or hives.")
    return "\n".join(lines + ["", "SAFETY NOTES:"] + [f"- {n}" for n in notes])


# ----------------------------------------------------------------- tool 2: product matching
def _evaluate(p, profile, wanted):
    """Return (score, exclusion_reason or None, flags)."""
    cap = irritation_cap(profile)
    haystack = " ".join([p["name"], p["brand"], *p["actives"], *p["key_ingredients"]]).lower()
    for t in avoid_terms(profile):
        if t in haystack and not any(w in t for w in FRAGRANCE_WORDS):
            return 0, f"contains or is built around '{t}' (on your avoid list)", []
    if _fragrance_strict(profile) and p["fragrance_free"] is not True:
        return 0, "fragrance-free status not confirmed (you listed fragrance as something to avoid)", []
    if profile.get("pregnant") and any(INGREDIENTS[a]["pregnancy"] == "avoid" for a in p["actives"]):
        return 0, "contains an ingredient not recommended in pregnancy / breastfeeding", []
    if p["irritation"] > cap:
        return 0, f"irritation level {p['irritation']} is above your cap of {cap}", []

    score, flags = 0, []
    for c in profile.get("concerns", []):
        for ing, w in CONCERNS[c]["ingredients"]:
            if ing in p["actives"]:
                score += w
    score += 2 * sum(1 for ing in wanted if ing in p["actives"])
    score += 2 if profile.get("skin_type") in p["skin_types"] else -2
    if _sensitive_mode(profile):
        score += {True: 2, False: -4, None: -1}[p["fragrance_free"]]
    if profile.get("region") == "India" and p["india"] is True:
        score += 1
    if profile.get("pregnant") and any(INGREDIENTS[a]["pregnancy"] == "ask_doctor" for a in p["actives"]):
        flags.append("ask your doctor first (pregnancy/breastfeeding)")
    if p["irritation"] >= 3:
        flags.append("strong active: start slowly")
    return score, None, flags


def _live_check(p, profile):
    """Look the product up on Open Beauty Facts and screen its ingredient list."""
    try:
        r = requests.get(OBF_URL, params={"search_terms": f"{p['brand']} {p['name']}", "search_simple": 1,
                                          "action": "process", "json": 1, "page_size": 6},
                         headers={"User-Agent": "SkinPilot/1.0 (student project)"}, timeout=12)
        r.raise_for_status()
        brand = re.sub(r"[^a-z0-9]", "", p["brand"].lower())
        for item in r.json().get("products", []):
            text = (item.get("ingredients_text") or "").lower()
            if text and brand in re.sub(r"[^a-z0-9]", "", (item.get("brands") or "").lower()):
                found = []
                for label, terms in (("fragrance", FRAGRANCE_TERMS), ("drying alcohol", ALCOHOL_TERMS),
                                     ("essential-oil / menthol type", ESSENTIAL_OIL_TERMS)):
                    hits = [t for t in terms if t in text]
                    if hits:
                        found.append(f"{label}: {', '.join(hits[:3])}")
                user_hits = [t for t in avoid_terms(profile) if t in text]
                if user_hits:
                    found.append(f"YOUR AVOID LIST: {', '.join(user_hits)}")
                return "listing found; " + ("; ".join(found) if found else "none of the screened irritant terms")
        return "no ingredient listing found online (read the pack)"
    except Exception:
        return "live lookup unavailable (read the pack)"


def find_products(profile, product_type, ingredients=""):
    product_type = (product_type or "").strip().lower()
    if product_type not in PRODUCT_TYPES:
        return f"ERROR: product_type must be one of {', '.join(PRODUCT_TYPES)}."
    asked = [i.strip() for i in re.split(r"[,;]", ingredients or "") if i.strip()]
    known = {k.lower(): k for k in INGREDIENTS}
    wanted = [known[a.lower()] for a in asked if a.lower() in known]
    unknown = [a for a in asked if a.lower() not in known]

    ranked, excluded = [], []
    for p in CATALOG:
        if p["type"] != product_type:
            continue
        score, why, flags = _evaluate(p, profile, wanted)
        if why:
            excluded.append((p["name"], why))
        else:
            ranked.append((score, p, flags))
    ranked.sort(key=lambda x: -x[0])
    top = ranked[:4]
    with ThreadPoolExecutor(max_workers=3) as ex:
        checks = list(ex.map(lambda t: _live_check(t[1], profile), top[:3]))
    checks += ["not checked (outside the top 3)"] * (len(top) - len(checks))

    rows = []
    for (score, p, flags), chk in zip(top, checks):
        rows.append((p["name"], ", ".join(p["actives"]) or "none (gentle base formula)", score,
                     _tf(p["fragrance_free"]), p["irritation"], _tf(p["india"]),
                     "; ".join([p["note"], *flags]), chk))
    out = [f"PRODUCT MATCHES: {product_type.upper()} (from the built-in example catalogue of "
           f"{len(CATALOG)} products; fit score is a simple rule-based number, not a quality rating)"]
    if rows:
        out.append(_md(["product", "key actives", "fit score", "fragrance-free", "irritation 0-3",
                        "likely sold in India", "notes and cautions", "online ingredient check"], rows))
    else:
        out.append("No suitable product in the catalogue for this profile. Advise the user which ingredients to look "
                   "for on labels instead, and to ask a pharmacist or dermatologist.")
    if excluded:
        out += ["", "SKIPPED FOR THIS PROFILE:", _md(["product", "reason"], excluded[:6])]
    if unknown:
        out.append(f"(Ignored unknown ingredient names: {', '.join(unknown)})")
    out.append("Always verify the full ingredient list on the pack: formulas change and the catalogue is not exhaustive. "
               "Online ingredient checks come from a community database and may be missing or outdated.")
    return "\n".join(out)


# ----------------------------------------------------------------- tool 3: routine builder
def _match_product(name):
    n = name.strip().lower()
    for p in CATALOG:
        pn = p["name"].lower()
        if n == pn or n in pn or pn in n:
            return p
    return None


def build_routine(profile, product_names):
    names = [n.strip() for n in re.split(r"[;\n]|,(?=\s*[A-Z])", product_names or "") if n.strip()]
    chosen, missing = [], []
    for n in names:
        p = _match_product(n)
        (chosen if p else missing).append(p or n)
    if not chosen:
        return "ERROR: none of the product names matched the catalogue. Use exact names from find_products results."

    by_type = {t: [p for p in chosen if p["type"] == t] for t in PRODUCT_TYPES}
    treatments = by_type["treatment"]

    def has(p, ing):
        return ing in p["actives"]

    retinoids = [p for p in treatments if has(p, "retinol") or has(p, "adapalene")]
    am_t, pm_t, notes = [], [], []
    for p in treatments:
        if has(p, "retinol") or has(p, "adapalene"):
            pm_t.append((p, "nights, start 2 nights a week"))
        elif has(p, "benzoyl peroxide"):
            (am_t if retinoids else pm_t).append((p, "start every other day" + (" (kept apart from your retinoid)" if retinoids else "")))
        elif has(p, "salicylic acid"):
            pm_t.append((p, "alternate nights with your retinoid" if retinoids else "start 2-3 nights a week"))
        elif has(p, "vitamin C"):
            am_t.append((p, "mornings, under sunscreen"))
        else:  # niacinamide, azelaic acid, etc.
            am_t.append((p, "mornings (can also be used at night)"))

    def names_of(items):
        return [f"{p['name']} ({how})" for p, how in items]

    cleanser = [p["name"] for p in by_type["cleanser"]]
    moist = [p["name"] for p in by_type["moisturizer"]]
    sun = [p["name"] for p in by_type["sunscreen"]]
    am = (cleanser[:1] or ["Gentle cleanse or water rinse"]) + names_of(am_t) + (moist[:1] or ["Moisturiser (add one)"]) \
        + (sun[:1] or ["Broad-spectrum SPF 30+ sunscreen (add one: essential)"])
    pm = (cleanser[:1] or ["Gentle cleanse"]) + names_of(pm_t) + (moist[:1] or ["Moisturiser (add one)"])

    strong = [p for p in treatments if p["irritation"] >= 2]
    if len(strong) > 2:
        notes.append("More than two moderate/strong actives: this is too many to start together. Follow the phased plan "
                     "below and drop the least important one if irritation appears.")
    for a, b, msg in (("benzoyl peroxide", "retinol", "benzoyl peroxide can break down retinol: keep them at different times of day"),
                      ("vitamin C", "retinol", "vitamin C in the morning and retinol at night works better than layering them"),
                      ("salicylic acid", "retinol", "do not use salicylic acid and retinol on the same night"),
                      ("salicylic acid", "adapalene", "do not use salicylic acid and adapalene on the same night")):
        if any(has(p, a) for p in treatments) and any(has(p, b) for p in treatments):
            notes.append(msg[0].upper() + msg[1:] + ".")
    if not by_type["sunscreen"]:
        notes.append("No sunscreen chosen: add one, because many of these actives increase sun sensitivity.")

    phases = ["Weeks 1-2: cleanser, moisturiser and sunscreen only, to settle the skin barrier. Patch-test every new product."]
    for i, p in enumerate(treatments):
        start = 3 + 2 * i
        phases.append(f"From week {start}: add {p['name']} ({'2-3 times a week' if p['irritation'] >= 2 else 'every other day, then daily'}), "
                      "and add nothing else for 2 weeks.")
    phases.append("Weeks 8-12: judge results honestly. Acne and pigmentation need about 8-12 weeks; see a dermatologist if there is no clear improvement.")
    out = ["SUGGESTED ROUTINE", "", "MORNING:"] + [f"{i}. {s}" for i, s in enumerate(am, 1)] + \
          ["", "EVENING:"] + [f"{i}. {s}" for i, s in enumerate(pm, 1)] + \
          ["", "INTRODUCTION PLAN:"] + [f"- {s}" for s in phases]
    if notes:
        out += ["", "INTERACTION / SAFETY NOTES:"] + [f"- {n}" for n in notes]
    if missing:
        out += ["", f"Names not found in the catalogue (ignored): {', '.join(missing)}"]
    return "\n".join(out)
