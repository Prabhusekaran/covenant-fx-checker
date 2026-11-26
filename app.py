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

    eur_usd_rate = quote["rate"]

    st.subheader("inputs")
    eur_debt = st.number_input("EUR debt (EUR m)", min_value=0.0, value=12.0, format="%.2f")
    usd_debt = st.number_input("USD debt (USD m)", min_value=0.0, value=10.0, format="%.2f")
    eur_cash = st.number_input("EUR cash (EUR m)", min_value=0.0, value=0.0, format="%.2f")
    ebitda = st.number_input("EUR EBITDA (EUR m)", value=6.0, format="%.2f")
    covenant_limit = st.number_input(
        "Covenant limit (net debt / EBITDA, x)", min_value=0.0, value=3.50, format="%.2f"
    )

    st.subheader("Illustrative FX covenant sensitivity — instant shock scenario")
    result = calc.covenant_check(
        eur_debt=eur_debt,
        usd_debt=usd_debt,
        eur_usd_rate=eur_usd_rate,
        ebitda=ebitda,
        cash_eur=eur_cash,
        covenant_limit=covenant_limit,
    )
    if result["leverage"] == calc.NOT_MEANINGFUL:
        st.warning(
            f"### {calc.NOT_MEANINGFUL}\n\n"
            "EUR EBITDA is zero or negative, so leverage against the covenant limit "
            "and headroom are not meaningful."
        )
    else:
        st.write(
            f"Debt stack (EUR debt + USD debt at {eur_usd_rate:.4f}): "
            f"**{result['debt_stack_eur']:.2f}** EUR m"
        )
        st.write(f"Net debt: **{result['net_debt_eur']:.2f}** EUR m")
        st.write(
            f"Leverage: **{result['leverage']:.2f}x** against covenant limit "
            f"**{covenant_limit:.2f}x**"
        )
        st.write(f"Headroom: **{result['headroom_eur']:.2f}** EUR m (negative = breach)")
