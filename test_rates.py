import datetime as dt
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

import rates

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "ecb_exr_D.USD.EUR.SP00.A.json"


def sdmx_payload(pairs):
    """Build a fake ECB Data API SDMX-JSON 1.0.0-wd payload from [(iso_date, rate), ...]."""
    return {
        "header": {"id": "mock", "test": True, "prepared": "2025-11-21T16:00:00+00:00"},
        "dataSets": [
            {
                "series": {
                    "0:0:0:0:0": {
                        "observations": {
                            str(i): [rate] for i, (_, rate) in enumerate(pairs)
                        }
                    }
                }
            }
        ],
        "structure": {
            "name": "ECB Data API mock",
            "dimensions": {
                "observation": [
                    {
                        "id": "TIME_PERIOD",
                        "values": [{"id": iso_date} for iso_date, _ in pairs],
                    }
                ]
            },
        },
    }


def test_weekend_falls_back_to_friday():
    friday = date(2025, 11, 21)
    sunday = date(2025, 11, 23)
    payload = sdmx_payload([("2025-11-20", 1.1500), ("2025-11-21", 1.1523)])
    with patch.object(rates, "_http_get_json", return_value=payload) as mock_get:
        result = rates.ecb_rate_for("USD", sunday)
    assert result["rate"] == 1.1523
    assert result["date"] == friday
    assert result["requested_date"] == sunday
    url = mock_get.call_args[0][0]
    assert "D.USD.EUR.SP00.A" in url
    assert "endPeriod=2025-11-23" in url


def test_target_holiday_falls_back_to_previous_business_day():
    new_years_day = date(2026, 1, 1)
    last_business_day = date(2025, 12, 31)
    payload = sdmx_payload([("2025-12-30", 1.1600), ("2025-12-31", 1.1601)])
    with patch.object(rates, "_http_get_json", return_value=payload):
        result = rates.ecb_rate_for("USD", new_years_day)
    assert result["rate"] == 1.1601
    assert result["date"] == last_business_day
    assert result["requested_date"] == new_years_day


def test_business_day_returns_same_day_and_normalizes_currency():
    friday = date(2025, 11, 21)
    payload = sdmx_payload([("2025-11-21", 1.1523)])
    with patch.object(rates, "_http_get_json", return_value=payload) as mock_get:
        result = rates.ecb_rate_for("usd", friday)
    assert result["rate"] == 1.1523
    assert result["date"] == friday
    assert result["currency"] == "USD"
    assert "D.USD.EUR.SP00.A" in mock_get.call_args[0][0]


def test_unknown_currency_raises_value_error():
    error = rates.EcbApiError("ECB Data API returned HTTP 404", status=404)
    with patch.object(rates, "_http_get_json", side_effect=error):
        with pytest.raises(ValueError, match="Unknown currency 'XXX'"):
            rates.ecb_rate_for("XXX", date(2025, 11, 21))


def test_malformed_currency_raises_value_error_without_network():
    with pytest.raises(ValueError, match="3-letter ISO code"):
        rates.ecb_rate_for("DOLLAR", date(2025, 11, 21))


def test_api_failure_raises_ecb_api_error():
    error = rates.EcbApiError("ECB Data API returned HTTP 500", status=500)
    with patch.object(rates, "_http_get_json", side_effect=error):
        with pytest.raises(rates.EcbApiError, match="HTTP 500"):
            rates.ecb_rate_for("USD", date(2025, 11, 21))


def test_empty_response_raises_instead_of_inventing_a_rate():
    with patch.object(rates, "_http_get_json", return_value=sdmx_payload([])):
        with pytest.raises(rates.EcbApiError, match="no USD reference rates"):
            rates.ecb_rate_for("USD", date(2025, 11, 21))


def test_accept_header_is_the_documented_sdmx_json_1_0_0_wd():
    assert rates.ACCEPT_SDMX_JSON == "application/vnd.sdmx.data+json;version=1.0.0-wd"


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_request_sends_the_documented_accept_header():
    payload = sdmx_payload([("2025-11-21", 1.1523)])
    with patch("urllib.request.urlopen", return_value=_FakeResponse(payload)) as mock_urlopen:
        result = rates.ecb_rate_for("USD", date(2025, 11, 21))
    request = mock_urlopen.call_args[0][0]
    assert request.get_header("Accept") == "application/vnd.sdmx.data+json;version=1.0.0-wd"
    assert result["rate"] == 1.1523
    assert result["date"] == date(2025, 11, 21)


def test_real_ecb_response_fixture_parses():
    """Parse one real, unmodified ECB Data API response saved under fixtures/.

    Captured live from
    https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2026-11-09&endPeriod=2026-11-26
    with Accept: application/vnd.sdmx.data+json;version=1.0.0-wd
    (the API answered Content-Type: application/vnd.sdmx.data+json;version=1.0.0-wd).
    """
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert "structure" in payload
    assert "structures" not in payload
    observations = rates._parse_observations(payload)
    assert observations
    for period, rate in observations.items():
        assert dt.date.fromisoformat(period)
        assert isinstance(rate, float) and rate > 0
    latest_period = max(observations)
    with patch.object(rates, "_http_get_json", return_value=payload):
        result = rates.ecb_rate_for("USD", dt.date.fromisoformat(latest_period))
        next_day = rates.ecb_rate_for(
            "USD", dt.date.fromisoformat(latest_period) + dt.timedelta(days=1)
        )
    assert result["rate"] == observations[latest_period]
    assert result["date"] == dt.date.fromisoformat(latest_period)
    assert next_day["date"] == dt.date.fromisoformat(latest_period)
    assert next_day["rate"] == observations[latest_period]
