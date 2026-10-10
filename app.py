1import streamlit as st
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

import skin_tools as stools
from knowledge import CONCERNS, DIAGNOSED

APP_TITLE = "SkinPilot"
FALLBACK_MODELS = ["gemini-3.7-flash", "gemini-3.6-flash"]  # tried if the chosen model hits its free quota

st.set_page_config(page_title=APP_TITLE, page_icon="🧴", layout="wide")

SYSTEM_PROMPT = """
You are SkinPilot, a skincare RESEARCH agent. You help a person understand which evidence-backed
skincare ingredients and example products fit their skin type and concerns. You are NOT a doctor and
you do not diagnose. You never replace advice from a dermatologist.

Workflow rules:
1. Step 1: call analyze_skin_profile once.
2. Step 2: using its ingredient strategy, call find_products once for each of the four product types
   (cleanser, moisturizer, sunscreen, treatment) in the same step. For treatment, pass the top-priority
   ingredient names from the strategy (exactly as written in the table) in the `ingredients` argument.
   Skip a type only if the user's profile clearly rules it out.
3. Step 3: choose ONE product per type from the find_products results (best fit score that has no
   serious caution), then call build_routine once with those exact product names separated by semicolons.
4. Never recommend a product, ingredient, strength, price, rule or fact that does not appear in tool
   output. Do not invent brands, ingredients, studies or availability. If find_products returns no
   suitable product, say so and tell the user which ingredients to look for on a label.
5. Safety first: put the "see a doctor" guidance and the diagnosed-condition note near the top. Never
   suggest prescription drugs (steroids, tretinoin, hydroquinone, antibiotics) as things to use; you may
   say a doctor can prescribe options. Respect pregnancy flags exactly as the tools state them.
6. Use neutral language: "may help", "evidence is strong/moderate/limited". Do not promise results or
   cures, and give honest timelines (acne and pigmentation take about 8-12 weeks).
7. Explain WHY each product fits (cite the actives, fit score, fragrance and irritation info) and its
   main caution. Mention the online ingredient check result and remind the user to read the pack.
8. Be kind and clear; avoid jargon or explain it.

Final answer format (Markdown), with these headings:
- Your profile (as provided)
- Safety first (red flags, when to see a doctor, patch-test advice)
- Ingredient strategy (what to look for and why, with evidence level)
- Recommended products (a table: type, product, key actives, why it fits you, caution)
- Products and ingredients to skip for you
- Your routine (morning and evening) and the step-by-step introduction plan
- What to expect and when to reassess
- Limitations
- Disclaimer: educational information only, not medical advice; verify ingredient lists on the pack;
  consult a dermatologist for diagnosis or persistent, painful or worsening skin problems.
Keep it clear and appropriately concise.
"""


def _last_text(result):
    for message in reversed(result.get("messages", [])):
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            parts = [i.get("text", "") for i in content
                     if isinstance(i, dict) and i.get("type") == "text"]
            if parts:
                return "\n".join(parts)
    return "The agent did not return a report. Please try again."


def run_agent(profile, api_key, model_name):
    tool_log = []  # raw tool outputs, shown to the user so every claim can be checked

    def log(name, text):
        tool_log.append((name, text))
        return text

    @tool
    def analyze_skin_profile() -> str:
        """Analyse the user's skin profile: returns the prioritised ingredient strategy (evidence, typical
        strength, irritation level, pregnancy notes), ingredients held back or excluded, red flags for when to
        see a doctor, and safety notes. Call this first."""
        return log("analyze_skin_profile", stools.analyze_profile(profile))

    @tool
    def find_products(product_type: str, ingredients: str = "") -> str:
        """Find and rank example products for this user. product_type must be one of: cleanser, moisturizer,
        sunscreen, treatment. ingredients is an optional comma-separated list of ingredient names taken from the
        ingredient strategy table (for example 'niacinamide, azelaic acid'). Returns ranked products with fit
        score, fragrance and irritation info, cautions, products skipped for this user and an online ingredient
        check."""
        return log(f"find_products({product_type})", stools.find_products(profile, product_type, ingredients))

    @tool
    def build_routine(product_names: str) -> str:
        """Build a morning and evening routine with a phased introduction plan and interaction warnings.
        product_names is a semicolon-separated list of exact product names chosen from find_products results."""
        return log("build_routine", stools.build_routine(profile, product_names))

    user_msg = (
        "Please create a personalised skincare research report for this person.\n"
        f"Skin type: {profile['skin_type']}\n"
        f"Concerns: {', '.join(profile['concerns']) or 'none selected'}\n"
        f"Doctor-diagnosed conditions: {', '.join(profile['diagnosed']) or 'none'}\n"
        f"Pregnant / breastfeeding / trying to conceive: {'yes' if profile['pregnant'] else 'no'}\n"
        f"Ingredients or allergens to avoid: {profile['avoid_text'] or 'none stated'}\n"
        f"Sensitive to fragrance: {'yes' if profile['fragrance_sensitive'] else 'no / not stated'}\n"
        f"Region: {profile['region']}\n"
        f"Current routine: {profile['current'] or 'not provided'}\n"
        f"Extra notes: {profile['notes'] or 'none'}"
    )

    chain = [model_name] + [m for m in FALLBACK_MODELS if m != model_name]
    last_exc = None
    for m in chain:
        try:
            llm = ChatGoogleGenerativeAI(model=m, temperature=0, google_api_key=api_key)
            agent = create_agent(model=llm, tools=[analyze_skin_profile, find_products, build_routine],
                                 system_prompt=SYSTEM_PROMPT)
            result = agent.invoke({"messages": [{"role": "user", "content": user_msg}]})
            return _last_text(result), tool_log, m
        except Exception as exc:
            if "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc):
                last_exc = exc  # free quota used up on this model: try the next one
                continue
            raise
    raise last_exc


# ------------------------------- UI ---------------------------------------
st.title("🧴 SkinPilot")
st.caption("An agentic skincare research assistant: it analyses your skin profile, checks safety rules, matches "
           "example products and builds a routine with a gradual introduction plan.")
st.warning("Educational information, **not medical advice**. SkinPilot cannot diagnose skin conditions. See a "
           "dermatologist for diagnosis, prescription treatment, or any skin problem that is painful, spreading, "
           "bleeding, infected or getting worse. Only enter details you are comfortable sharing: your profile is sent to the Gemini API.")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Gemini API key", type="password",
        help="Free key from https://aistudio.google.com/apikey. Never paste it into source code or commit it.",
    )
    model_name = st.text_input("Model", value="gemini-3.8-flash")
    st.caption("A report uses roughly 4 model requests. The free tier has a small daily quota per model; "
               "the app falls back to other Gemini models automatically.")
    st.caption("Your profile is sent to the Gemini API to write the report.")

left, right = st.columns(2)
with left:
    skin_type = st.selectbox("Skin type", ["Oily", "Combination", "Normal", "Dry", "Sensitive"], index=1)
    concerns = st.multiselect("Main concerns", list(CONCERNS.keys()), default=["Acne / breakouts"])
    diagnosed = st.multiselect("Conditions diagnosed by a doctor (if any)", DIAGNOSED)
    region = st.selectbox("Where will you buy?", ["India", "Other"])
with right:
    pregnant = st.checkbox("Pregnant, breastfeeding or trying to conceive")
    fragrance_sensitive = st.checkbox("My skin reacts to fragrance")
    avoid_text = st.text_input("Ingredients / allergens to avoid (comma separated)", placeholder="e.g. fragrance, lanolin, coconut oil")
    current = st.text_area("What do you use now? (optional)", height=70,
                           placeholder="e.g. a face wash, Cetaphil lotion, sometimes vitamin C serum")
    notes = st.text_input("Anything else we should know? (optional)")

if st.button("Generate skincare report", type="primary", disabled=not concerns):
    if not api_key.strip():
        st.error("Enter your Gemini API key in the sidebar.")
    else:
        profile = dict(skin_type=skin_type, concerns=concerns, diagnosed=diagnosed, pregnant=pregnant,
                       fragrance_sensitive=fragrance_sensitive, avoid_text=avoid_text.strip(),
                       current=current.strip(), notes=notes.strip(), region=region)
        with st.spinner("Analysing your profile, matching products and writing the report (can take 1-2 minutes)..."):
            try:
                report, log, used = run_agent(profile, api_key.strip(), model_name.strip())
                st.session_state.update(last_report=report, last_log=log, last_model=used)
            except Exception as exc:
                st.error("The agent could not complete the run. Check your Gemini API key, model name, internet "
                         "connection and package versions. If it says RESOURCE_EXHAUSTED / 429, the free daily "
                         "quota is used up on all tried models: wait for the reset or try another model name. "
                         "Technical message:")
                st.code(str(exc))

if st.session_state.get("last_report"):
    st.divider()
    st.subheader("Your skincare report")
    st.caption(f"Written by {st.session_state.get('last_model')}")
    st.markdown(st.session_state["last_report"])
    st.download_button("Download report (.md)", data=st.session_state["last_report"],
                       file_name="skinpilot_report.md", mime="text/markdown")
    with st.expander("Raw tool data the agent saw (check the report against this)"):
        for name, text in st.session_state.get("last_log", []):
            st.markdown(f"**{name}**")
            st.text(text)

with st.expander("How is this agentic?"):
    st.markdown(
        """
        - **Goal-driven tool use:** the model decides which tools to call and with which ingredients.
        - **Multi-step loop:** profile analysis, then product search for each product type, then routine building; each step uses the previous result.
        - **Grounding:** safety rules, scoring and interaction checks are deterministic Python, not LLM guesses, and the raw tables are shown for verification.
        - **Guardrails:** pregnancy exclusions, irritation caps, allergen filters, red-flag guidance and a no-diagnosis policy.
        - **Human in the loop:** you supply the profile and a clinician makes the medical decisions.
        """
    )
