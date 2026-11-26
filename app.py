import datetime as dt

import streamlit as st

import calc
import rates

st.title("Covenant FX Checker")

st.subheader("data: ECB reference rates")
today = dt.date.today()
try:
    quote = rates.ecb_rate_for("USD", today)
except rates.EcbApiError as exc:
    st.error(f"Could not load the ECB reference rate: {exc}")
else:
    st.write(f"EUR/USD reference rate: **{quote['rate']:.4f}**")
    st.write(f"Observation date (TARGET business day): **{quote['date'].isoformat()}**")
    if quote["date"] < today:
        st.info(
            f"No ECB rate for {today.isoformat()} yet (weekend/holiday or not published today); "
            f"showing the latest published rate, observed on {quote['date'].isoformat()}."
        )
