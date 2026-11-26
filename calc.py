"""Pure covenant maths for the Covenant FX Checker.

No Streamlit in this module. All money amounts are expressed in one shared
unit (the tests use millions), EUR after translation where the name says _eur.
"""

NOT_MEANINGFUL = "not meaningful"


def usd_to_eur(amount_usd, eur_usd_rate):
    """Translate a USD amount to EUR at the given EUR/USD rate."""
    if eur_usd_rate <= 0:
        raise ValueError("EUR/USD rate must be positive")
    return amount_usd / eur_usd_rate


def debt_stack_eur(eur_debt, usd_debt, eur_usd_rate):
    """Gross debt stack in EUR: EUR debt plus USD debt translated at the rate."""
    return eur_debt + usd_to_eur(usd_debt, eur_usd_rate)


def net_debt_eur(eur_debt, usd_debt, eur_usd_rate, cash_eur=0.0):
    """Total net debt in EUR: the debt stack minus cash."""
    return debt_stack_eur(eur_debt, usd_debt, eur_usd_rate) - cash_eur


def leverage(net_debt, ebitda):
    """Net debt divided by EBITDA; 'not meaningful' when EBITDA is zero or negative."""
    if ebitda <= 0:
        return NOT_MEANINGFUL
    return net_debt / ebitda


def headroom_eur(net_debt, ebitda, covenant_limit):
    """EUR headroom against the covenant: limit * EBITDA - net debt (negative = breach)."""
    if ebitda <= 0:
        return NOT_MEANINGFUL
    return covenant_limit * ebitda - net_debt


def covenant_check(eur_debt, usd_debt, eur_usd_rate, ebitda, cash_eur, covenant_limit):
    """Convenience wrapper: debt stack, net debt, leverage and headroom in one dict."""
    stack = debt_stack_eur(eur_debt, usd_debt, eur_usd_rate)
    debt = stack - cash_eur
    return {
        "debt_stack_eur": stack,
        "net_debt_eur": debt,
        "leverage": leverage(debt, ebitda),
        "headroom_eur": headroom_eur(debt, ebitda, covenant_limit),
    }
