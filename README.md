# SkinPilot: Agentic Skincare Research Assistant

SkinPilot is a Streamlit app where a Gemini-powered agent analyses your skin type and concerns, applies safety rules, matches example skincare products and builds a morning/evening routine with a gradual introduction plan.

> **Disclaimer:** educational information only, not medical advice. SkinPilot cannot diagnose skin conditions. See a dermatologist for diagnosis, prescription treatment, or any problem that is painful, spreading, bleeding, infected or getting worse. Always read the ingredient list on the pack.

## How it works

1. You enter skin type, concerns, doctor-diagnosed conditions, pregnancy status, allergens to avoid, and your current routine.
2. The agent (LangChain + Gemini) calls three tools in sequence:
   - `analyze_skin_profile`: prioritised ingredient strategy (evidence level, typical strength, irritation level), held-back and excluded ingredients, red flags for when to see a doctor.
   - `find_products` (called per product type): ranks example products from a curated catalogue, filters out unsuitable ones with reasons, and optionally checks ingredient lists on Open Beauty Facts.
   - `build_routine`: AM/PM routine, phased introduction plan, and interaction warnings (for example benzoyl peroxide with retinol).
3. All rules, scoring and filtering are plain Python (`skin_tools.py`, `knowledge.py`). **The LLM never invents products, strengths or rules**; it chooses tools and explains the results.
4. The raw tool tables are shown in the app so you can check the report.

### Safety logic
- Irritation cap: sensitive skin, rosacea-like redness, eczema-prone skin and psoriasis / seborrheic dermatitis lower the strength of actives allowed.
- Pregnancy / breastfeeding: retinoids are excluded; other actives are flagged "ask your doctor first".
- Your avoid list (for example fragrance, lanolin) filters products; "fragrance" requires a confirmed fragrance-free product.
- Diagnosed conditions: products are positioned as supportive care only, never as a replacement for prescribed treatment.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```
Get a free Gemini key at https://aistudio.google.com/apikey and paste it in the sidebar. A report uses about 4 model requests; the app falls back to other Gemini models if one hits its free daily quota.

## Project structure

```text
skinpilot_agent/
├── app.py           # Streamlit UI + Gemini agent + tool definitions
├── skin_tools.py    # deterministic logic: safety rules, scoring, routine builder, label check
├── knowledge.py     # ingredient facts, concern mappings, example product catalogue (editable data)
├── requirements.txt
├── README.md
├── schema.md        # workflow diagram and JSON schema
└── .gitignore
```

## Limitations

- The catalogue is a small, hand-written list of example products from general knowledge. Formulas, names and availability change: verify everything on the pack. Extend `CATALOG` in `knowledge.py` with products you trust.
- Open Beauty Facts is community-edited; a missing listing means "not found", not "safe" or "unsafe".
- Ingredient guidance is general and widely published, not personalised medical advice; strengths and evidence levels should be confirmed with a dermatologist.
- No skin photos are analysed, and no diagnosis is attempted.
- Prices and exact availability are not covered.

## Attribution

Built with Streamlit, LangChain, Google Gemini and Open Beauty Facts, adapted from the same agent pattern as the earlier ResearchPilot and InvestPilot projects. Understand the key functions (`_evaluate`, `irritation_cap`, `build_routine`) before presenting.
