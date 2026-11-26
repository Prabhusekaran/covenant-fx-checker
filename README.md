# Illustrative FX covenant sensitivity tool

Covenant FX Checker — a Streamlit skeleton showing how EUR/USD rate moves change
leverage and covenant headroom for an illustrative company with EUR and USD debt
and EUR-denominated EBITDA.

## Files

- `calc.py` — all the maths as pure functions (no Streamlit code in it).
- `rates.py` — live ECB reference rates from the ECB Data API, requested as SDMX-JSON
  `application/vnd.sdmx.data+json;version=1.0.0-wd`, with TARGET business-day fallback.
- `app.py` — thin Streamlit app; shows today's EUR/USD ECB reference rate and its
  observation date.
- `test_calc.py`, `test_rates.py` — pytest suite. `test_rates.py` also parses a real,
  unmodified ECB response saved in `fixtures/`.
- `.github/workflows/pytest.yml` — runs the full pytest suite on every pull request.

## Run

```bash
pip install -r requirements.txt pytest
streamlit run app.py
pytest
```

`fixtures/ecb_exr_D.USD.EUR.SP00.A.json` is a real ECB Data API response captured from
`https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2026-11-09&endPeriod=2026-11-26`
with `Accept: application/vnd.sdmx.data+json;version=1.0.0-wd`.

All figures are illustrative only.
