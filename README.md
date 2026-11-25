# Illustrative FX covenant sensitivity tool

Covenant FX Checker — a Streamlit skeleton showing how EUR/USD rate moves change
leverage and covenant headroom for an illustrative company with EUR and USD debt
and EUR-denominated EBITDA.

## Files

- `calc.py` — all the maths as pure functions (no Streamlit code in it).
- `app.py` — thin Streamlit placeholder; imports `calc.py` and shows a title.
- `test_calc.py` — acceptance tests with hardcoded FX rates (no live rate fetching yet).

## Run

```bash
pip install streamlit pytest
streamlit run app.py
pytest
```

All figures are illustrative only.
