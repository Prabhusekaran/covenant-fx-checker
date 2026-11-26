"""ECB reference rates for the Covenant FX Checker.

Rates come from the free ECB Data API (data-api.ecb.europa.eu), dataflow EXR,
key D.<CCY>.EUR.SP00.A: the daily ECB reference rate quoted as units of <CCY>
per 1 EUR. The ECB publishes only on TARGET business days, so a weekend or
holiday request falls back to the most recent published observation on or
before the requested date.
"""

import datetime as dt
import json
import re
import urllib.error
import urllib.request

ECB_DATA_API = "https://data-api.ecb.europa.eu/service/data/EXR"
ACCEPT_SDMX_JSON = "application/vnd.sdmx.data+json;version=1.0.0-wd"
LOOKBACK_DAYS = 31
CURRENCY_RE = re.compile(r"^[A-Za-z]{3}$")


class EcbApiError(RuntimeError):
    """The ECB Data API could not be reached or returned an unusable response."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def _http_get_json(url):
    """GET `url` from the ECB Data API and return the decoded JSON payload."""
    request = urllib.request.Request(url, headers={"Accept": ACCEPT_SDMX_JSON})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise EcbApiError(
            f"ECB Data API returned HTTP {exc.code} for {url}", status=exc.code
        ) from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise EcbApiError(f"ECB Data API request failed for {url}: {exc}") from exc


def _parse_observations(payload):
    """Extract {TIME_PERIOD string: rate} from an SDMX-JSON payload (1.0.0-wd or 2.0 shape)."""
    observations = {}
    for data_set in payload.get("dataSets") or []:
        for series in (data_set.get("series") or {}).values():
            observations.update(series.get("observations") or {})
    structures = payload.get("structures")
    if structures is None and "structure" in payload:
        structures = [payload["structure"]]
    time_periods = []
    for structure in structures or []:
        dimensions = (structure.get("dimensions") or {}).get("observation") or []
        for dimension in dimensions:
            if dimension.get("id") == "TIME_PERIOD":
                time_periods = [value["id"] for value in dimension.get("values") or []]
    parsed = {}
    for index, observation in observations.items():
        period = time_periods[int(index)]
        value = observation[0] if isinstance(observation, (list, tuple)) else observation
        parsed[period] = float(value)
    return parsed


def ecb_rate_for(currency, date):
    """Return the ECB EUR reference rate for `currency` on `date`.

    Returns a dict with:
      - "rate": units of `currency` per 1 EUR,
      - "date": the TARGET business day the rate was actually published on
        (earlier than the requested date when that date was a weekend/holiday),
      - "requested_date": the date that was asked for,
      - "currency": the uppercased ISO code.

    Raises ValueError for an unknown or malformed currency and EcbApiError
    when the API fails or has no data; it never invents a rate.
    """
    if not isinstance(currency, str) or not CURRENCY_RE.match(currency):
        raise ValueError(
            f"Unknown currency {currency!r}: expected a 3-letter ISO code like 'USD'"
        )
    if not isinstance(date, dt.date):
        raise TypeError(f"date must be a datetime.date, got {type(date).__name__}")
    currency = currency.upper()
    end = date
    start = date - dt.timedelta(days=LOOKBACK_DAYS)
    url = (
        f"{ECB_DATA_API}/D.{currency}.EUR.SP00.A"
        f"?startPeriod={start.isoformat()}&endPeriod={end.isoformat()}"
    )
    try:
        payload = _http_get_json(url)
    except EcbApiError as exc:
        if exc.status == 404:
            raise ValueError(
                f"Unknown currency {currency!r}: the ECB publishes no EUR reference rate for it"
            ) from exc
        raise
    observations = _parse_observations(payload)
    eligible = {p: r for p, r in observations.items() if p <= end.isoformat()}
    if not eligible:
        raise EcbApiError(
            f"ECB Data API returned no {currency} reference rates on or before {end.isoformat()}"
        )
    latest_period = max(eligible)
    return {
        "currency": currency,
        "rate": eligible[latest_period],
        "date": dt.date.fromisoformat(latest_period),
        "requested_date": date,
    }
