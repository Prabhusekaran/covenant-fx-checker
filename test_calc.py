import calc

EUR_DEBT = 12.0
USD_DEBT = 10.0
EBITDA = 6.0
CASH = 0.0
COVENANT_LIMIT = 3.50


def test_leverage_and_headroom_at_eur_usd_1_20():
    result = calc.covenant_check(
        EUR_DEBT, USD_DEBT, eur_usd_rate=1.20, ebitda=EBITDA,
        cash_eur=CASH, covenant_limit=COVENANT_LIMIT,
    )
    assert round(result["leverage"], 2) == 3.39
    assert round(result["headroom_eur"], 2) == 0.67


def test_leverage_and_headroom_at_eur_usd_1_10():
    result = calc.covenant_check(
        EUR_DEBT, USD_DEBT, eur_usd_rate=1.10, ebitda=EBITDA,
        cash_eur=CASH, covenant_limit=COVENANT_LIMIT,
    )
    assert round(result["leverage"], 2) == 3.52
    assert round(result["headroom_eur"], 2) == -0.09


def test_ebitda_guard_returns_not_meaningful():
    assert calc.leverage(20.0, 0.0) == "not meaningful"
    assert calc.leverage(20.0, -2.0) == "not meaningful"
    assert calc.headroom_eur(20.0, 0.0, COVENANT_LIMIT) == "not meaningful"
