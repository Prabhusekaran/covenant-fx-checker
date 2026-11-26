from datetime import date
from unittest.mock import patch

import pytest

import rates


def sdmx_payload(pairs):
    """Build a fake ECB Data API SDMX-JSON v2 payload from [(iso_date, rate), ...]."""
    return {
        "dataSets": [
            {
                "series": {
                    "0:0:0:0:0:0:0": {
                        "observations": {
                            str(i): [rate] for i, (_, rate) in enumerate(pairs)
                        }
                    }
                }
            }
        ],
        "structures": [
            {
                "dimensions": {
                    "observation": [
                        {
                            "id": "TIME_PERIOD",
                            "values": [{"id": iso_date} for iso_date, _ in pairs],
                        }
                    ]
                }
            }
        ],
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
