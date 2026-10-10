"""Curated skincare knowledge base for SkinPilot.

This file is DATA, not logic: ingredient facts, concern -> ingredient mappings and a small
catalogue of example products. Edit it freely. Nothing here is medical advice; the strengths and
evidence levels are general, widely published guidance and should be confirmed with a dermatologist.
Product formulas change over time, so every product must be verified against the pack label.
"""

# pregnancy: "ok" | "ask_doctor" | "avoid"
INGREDIENTS = {
    "benzoyl peroxide": dict(
        evidence="strong", irritation=3, pregnancy="ask_doctor",
        strength="2.5-5% (higher strengths are not more effective, only more irritating)",
        notes="Antibacterial and unclogs pores. Bleaches fabrics and hair. Start every other day; dryness and peeling are common."),
    "adapalene": dict(
        evidence="strong", irritation=3, pregnancy="avoid",
        strength="0.1% (may need a prescription depending on the country)",
        notes="Topical retinoid for acne. Use at night; skin often looks worse for 4-8 weeks before it improves. Strict sun protection needed."),
    "retinol": dict(
        evidence="moderate", irritation=3, pregnancy="avoid",
        strength="start at 0.2-0.3%, build slowly towards 0.5%",
        notes="Helps fine lines and uneven tone over months. Night use only; start 2 nights a week; needs daily sunscreen."),
    "salicylic acid": dict(
        evidence="moderate", irritation=2, pregnancy="ask_doctor",
        strength="0.5-2%",
        notes="Oil-soluble BHA that unclogs pores; useful for blackheads and oiliness. Can dry the skin; start 2-3 times a week."),
    "azelaic acid": dict(
        evidence="moderate-strong", irritation=2, pregnancy="ask_doctor",
        strength="10% over the counter in many places (15-20% is prescription)",
        notes="Helps acne, redness and dark marks. Often better tolerated than retinoids; mild tingling at first is common."),
    "niacinamide": dict(
        evidence="moderate", irritation=1, pregnancy="ok",
        strength="2-5% is enough; very high strengths can irritate some people",
        notes="Supports the skin barrier and may reduce oiliness, redness and dark marks. Well tolerated by most people."),
    "vitamin C": dict(
        evidence="moderate", irritation=2, pregnancy="ok",
        strength="10-20% L-ascorbic acid, or stable derivatives",
        notes="Antioxidant that may brighten marks and add sun protection when used under sunscreen. Unstable: keep sealed, discard if dark brown."),
    "tranexamic acid": dict(
        evidence="limited-moderate", irritation=1, pregnancy="ask_doctor",
        strength="2-5% topical",
        notes="May help stubborn pigmentation; evidence is smaller than for azelaic acid or sunscreen."),
    "urea": dict(
        evidence="moderate-strong", irritation=1, pregnancy="ok",
        strength="5-10% for dry skin",
        notes="Hydrates and softens rough skin. Can sting on cracked or inflamed skin."),
    "ceramides": dict(
        evidence="moderate", irritation=0, pregnancy="ok", strength="in barrier moisturisers",
        notes="Skin-identical lipids that help repair the barrier; good for dry and eczema-prone skin."),
    "hyaluronic acid": dict(
        evidence="moderate", irritation=0, pregnancy="ok", strength="any",
        notes="Humectant that holds water in the surface of the skin; apply to damp skin and seal with a moisturiser."),
    "glycerin": dict(
        evidence="strong", irritation=0, pregnancy="ok", strength="any",
        notes="Reliable humectant found in most good moisturisers."),
    "colloidal oatmeal": dict(
        evidence="moderate", irritation=0, pregnancy="ok", strength="1% or as formulated",
        notes="Soothes itch and dryness; common in products for eczema-prone skin."),
    "panthenol": dict(
        evidence="limited-moderate", irritation=0, pregnancy="ok", strength="1-5%",
        notes="Provitamin B5; calming and moisturising."),
    "sunscreen": dict(
        evidence="strong", irritation=1, pregnancy="ok",
        strength="broad-spectrum SPF 30+ (SPF 50 for pigmentation), reapply every 2-3 hours outdoors",
        notes="The single most important product for dark marks and ageing. Mineral (zinc/titanium) filters are usually gentler on sensitive or rosacea-prone skin."),
    "AHA": dict(
        evidence="moderate", irritation=2, pregnancy="ask_doctor",
        strength="glycolic 5-10% or lactic 5-12%",
        notes="Water-soluble acids that smooth texture and fade marks; increase sun sensitivity."),
}

# concern -> weighted ingredient priorities (3 = first line, 1 = supportive)
CONCERNS = {
    "Acne / breakouts": dict(
        ingredients=[("benzoyl peroxide", 3), ("adapalene", 3), ("azelaic acid", 2), ("salicylic acid", 2), ("niacinamide", 1)],
        see_doctor="deep painful nodules or cysts, scarring, no clear improvement after 8-12 weeks of consistent use, "
                   "sudden severe acne, or acne with irregular periods or excess hair growth"),
    "Post-acne marks / dark spots": dict(
        ingredients=[("sunscreen", 3), ("azelaic acid", 3), ("niacinamide", 2), ("vitamin C", 2), ("tranexamic acid", 1), ("retinol", 1), ("AHA", 1)],
        see_doctor="a mole or dark spot that is changing, growing, bleeding or has an irregular border (see a doctor promptly), "
                   "symmetrical patches on the cheeks or forehead (possible melasma), or no improvement after about 3 months"),
    "Dry skin": dict(
        ingredients=[("ceramides", 3), ("glycerin", 2), ("hyaluronic acid", 2), ("urea", 2), ("panthenol", 1), ("colloidal oatmeal", 1)],
        see_doctor="cracking or bleeding skin, intense itch, or no improvement after 2 weeks of regular moisturising"),
    "Eczema-prone / very sensitive skin": dict(
        ingredients=[("ceramides", 3), ("colloidal oatmeal", 2), ("glycerin", 2), ("panthenol", 1), ("urea", 1)],
        see_doctor="weeping or crusted skin, rapidly spreading rash, signs of infection, itch that disturbs sleep, "
                   "or flares that need prescription treatment such as steroid creams"),
    "Redness / rosacea-like flushing": dict(
        ingredients=[("azelaic acid", 3), ("sunscreen", 3), ("niacinamide", 2), ("ceramides", 1)],
        see_doctor="persistent facial redness, flushing with bumps, burning, or eye irritation (rosacea has prescription treatments)"),
    "Oily skin / enlarged pores / blackheads": dict(
        ingredients=[("niacinamide", 3), ("salicylic acid", 3), ("azelaic acid", 1), ("glycerin", 1)],
        see_doctor="sudden change in oiliness together with other symptoms, or painful inflamed bumps"),
    "Fine lines / early ageing": dict(
        ingredients=[("sunscreen", 3), ("retinol", 3), ("vitamin C", 2), ("niacinamide", 1), ("hyaluronic acid", 1), ("AHA", 1)],
        see_doctor="a new or changing skin growth, or a sore that does not heal"),
}

DIAGNOSED = ["Eczema (atopic dermatitis)", "Rosacea", "Psoriasis", "Seborrheic dermatitis",
             "Another condition diagnosed by a doctor"]
GENTLE_ONLY = {"Eczema (atopic dermatitis)", "Psoriasis", "Seborrheic dermatitis"}

# words in free text that mean the user already uses an ingredient
ALIASES = {
    "retinol": ["retinol", "retinoid", "retinal", "tretinoin", "retin-a"],
    "adapalene": ["adapalene", "differin"],
    "benzoyl peroxide": ["benzoyl", "bpo", "panoxyl", "benzac"],
    "salicylic acid": ["salicylic", "bha"],
    "azelaic acid": ["azelaic"],
    "niacinamide": ["niacinamide"],
    "vitamin C": ["vitamin c", "ascorbic"],
    "AHA": ["glycolic", "lactic acid", "aha", "mandelic"],
}

FRAGRANCE_TERMS = ["parfum", "fragrance", "aroma", "linalool", "limonene", "geraniol", "citronellol",
                   "eugenol", "cinnamal", "coumarin", "benzyl salicylate", "hydroxycitronellal"]
ALCOHOL_TERMS = ["alcohol denat", "sd alcohol", "denatured alcohol", "isopropyl alcohol", "ethanol"]
ESSENTIAL_OIL_TERMS = ["essential oil", "lavandula", "mentha", "menthol", "camphor", "eucalyptus",
                       "melaleuca", "peppermint", "citrus aurantium"]

# Example products. actives use the INGREDIENTS names. fragrance_free / india: True, False or None (unknown).
# This is a starting catalogue from general knowledge: formulas, names and availability change.
CATALOG = [
    # ---- cleansers
    dict(name="CeraVe Foaming Facial Cleanser", brand="CeraVe", type="cleanser",
         actives=["niacinamide", "ceramides", "hyaluronic acid", "glycerin"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=True, irritation=0, india=True,
         note="Gel-foam cleanser for oily and combination skin."),
    dict(name="CeraVe Hydrating Facial Cleanser", brand="CeraVe", type="cleanser",
         actives=["ceramides", "hyaluronic acid", "glycerin"], key_ingredients=[],
         skin_types=["Dry", "Normal", "Sensitive"], fragrance_free=True, irritation=0, india=True,
         note="Non-foaming, creamy cleanser for dry or sensitive skin."),
    dict(name="Cetaphil Gentle Skin Cleanser", brand="Cetaphil", type="cleanser",
         actives=[], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal", "Dry", "Sensitive"], fragrance_free=True, irritation=0, india=True,
         note="Very simple, soap-free formula that suits most skin types."),
    dict(name="La Roche-Posay Toleriane Hydrating Gentle Cleanser", brand="La Roche-Posay", type="cleanser",
         actives=["ceramides", "niacinamide", "glycerin"], key_ingredients=[],
         skin_types=["Dry", "Normal", "Sensitive", "Combination"], fragrance_free=True, irritation=0, india=True,
         note="Gentle cleanser aimed at sensitive skin."),
    # ---- moisturisers
    dict(name="CeraVe Moisturising Cream", brand="CeraVe", type="moisturizer",
         actives=["ceramides", "hyaluronic acid", "glycerin"], key_ingredients=[],
         skin_types=["Dry", "Normal", "Sensitive"], fragrance_free=True, irritation=0, india=True,
         note="Rich cream, can feel heavy on oily skin."),
    dict(name="CeraVe PM Facial Moisturizing Lotion", brand="CeraVe", type="moisturizer",
         actives=["niacinamide", "ceramides", "hyaluronic acid", "glycerin"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal", "Sensitive"], fragrance_free=True, irritation=0, india=None,
         note="Lightweight lotion with niacinamide; suits oily and acne-prone skin."),
    dict(name="La Roche-Posay Toleriane Double Repair Face Moisturizer", brand="La Roche-Posay", type="moisturizer",
         actives=["ceramides", "niacinamide", "glycerin"], key_ingredients=[],
         skin_types=["Normal", "Dry", "Sensitive", "Combination"], fragrance_free=True, irritation=0, india=True,
         note="Light-to-medium moisturiser for sensitive skin."),
    dict(name="Cetaphil Moisturizing Cream", brand="Cetaphil", type="moisturizer",
         actives=["glycerin"], key_ingredients=["plant oils"],
         skin_types=["Dry", "Sensitive", "Normal"], fragrance_free=True, irritation=0, india=True,
         note="Rich cream for dry skin. Check the label for nut-derived oils if you have a nut allergy."),
    dict(name="Vanicream Moisturizing Cream", brand="Vanicream", type="moisturizer",
         actives=["glycerin"], key_ingredients=[],
         skin_types=["Dry", "Sensitive", "Normal"], fragrance_free=True, irritation=0, india=False,
         note="Free of common irritants (fragrance, dyes); popular for eczema-prone skin. May need importing."),
    # ---- sunscreens
    dict(name="EltaMD UV Clear Broad-Spectrum SPF 46", brand="EltaMD", type="sunscreen",
         actives=["sunscreen", "niacinamide"], key_ingredients=["zinc oxide", "octinoxate"],
         skin_types=["Oily", "Combination", "Normal", "Sensitive"], fragrance_free=True, irritation=1, india=False,
         note="Zinc oxide plus a chemical filter, with niacinamide; designed for acne- and rosacea-prone skin. May need importing."),
    dict(name="La Roche-Posay Anthelios UVMune 400 Invisible Fluid SPF 50+", brand="La Roche-Posay", type="sunscreen",
         actives=["sunscreen"], key_ingredients=["chemical filters"],
         skin_types=["Oily", "Combination", "Normal", "Dry", "Sensitive"], fragrance_free=True, irritation=1, india=True,
         note="Lightweight chemical-filter sunscreen with strong UVA protection."),
    dict(name="Neutrogena Sheer Zinc Face Dry-Touch Sunscreen SPF 50", brand="Neutrogena", type="sunscreen",
         actives=["sunscreen"], key_ingredients=["zinc oxide"],
         skin_types=["Oily", "Combination", "Normal", "Sensitive"], fragrance_free=None, irritation=1, india=None,
         note="Mineral (zinc oxide) option; may leave a slight cast on deeper skin tones."),
    dict(name="Re'equil Ultra Matte Dry Touch Sunscreen Gel SPF 50", brand="Re'equil", type="sunscreen",
         actives=["sunscreen"], key_ingredients=["chemical filters"],
         skin_types=["Oily", "Combination"], fragrance_free=None, irritation=1, india=True,
         note="Matte gel texture for oily skin in hot, humid climates."),
    # ---- treatments / serums
    dict(name="The Ordinary Niacinamide 10% + Zinc 1%", brand="The Ordinary", type="treatment",
         actives=["niacinamide"], key_ingredients=["zinc pca"],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=True, irritation=1, india=True,
         note="10% is higher than the 2-5% usually needed; begin every other day if your skin is sensitive."),
    dict(name="Minimalist 10% Niacinamide Face Serum", brand="Minimalist", type="treatment",
         actives=["niacinamide"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=True, irritation=1, india=True,
         note="Indian brand; 10% niacinamide serum."),
    dict(name="Paula's Choice Skin Perfecting 2% BHA Liquid Exfoliant", brand="Paula's Choice", type="treatment",
         actives=["salicylic acid"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=True, irritation=2, india=None,
         note="Leave-on salicylic acid for blackheads and pores."),
    dict(name="Minimalist 2% Salicylic Acid Face Serum", brand="Minimalist", type="treatment",
         actives=["salicylic acid"], key_ingredients=[],
         skin_types=["Oily", "Combination"], fragrance_free=True, irritation=2, india=True,
         note="Indian brand; 2% salicylic acid serum."),
    dict(name="The Ordinary Azelaic Acid Suspension 10%", brand="The Ordinary", type="treatment",
         actives=["azelaic acid"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal", "Dry", "Sensitive"], fragrance_free=True, irritation=2, india=True,
         note="Can feel gritty or pill under other products."),
    dict(name="Differin Gel (adapalene 0.1%)", brand="Differin", type="treatment",
         actives=["adapalene"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=None, irritation=3, india=None,
         note="May require a prescription in some countries (including possibly India): ask a pharmacist or doctor."),
    dict(name="Benzac AC Gel (benzoyl peroxide 2.5%)", brand="Benzac", type="treatment",
         actives=["benzoyl peroxide"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=None, irritation=3, india=True,
         note="Sold in several strengths; 2.5% is the sensible starting point. May be prescription-only locally."),
    dict(name="PanOxyl Acne Foaming Wash (benzoyl peroxide)", brand="PanOxyl", type="treatment",
         actives=["benzoyl peroxide"], key_ingredients=[],
         skin_types=["Oily", "Combination", "Normal"], fragrance_free=None, irritation=3, india=False,
         note="Wash-off format (short contact) is usually less irritating than a leave-on gel. May need importing."),
    dict(name="The Ordinary Retinol 0.2% in Squalane", brand="The Ordinary", type="treatment",
         actives=["retinol"], key_ingredients=["squalane"],
         skin_types=["Normal", "Dry", "Combination", "Oily"], fragrance_free=True, irritation=3, india=True,
         note="Beginner retinol strength; night use only."),
    dict(name="Timeless 20% Vitamin C + E + Ferulic Acid Serum", brand="Timeless", type="treatment",
         actives=["vitamin C"], key_ingredients=["ascorbic acid", "vitamin e", "ferulic acid"],
         skin_types=["Normal", "Oily", "Combination", "Dry"], fragrance_free=True, irritation=2, india=None,
         note="L-ascorbic acid serum; tingles on first use. Oxidises over time."),
]
