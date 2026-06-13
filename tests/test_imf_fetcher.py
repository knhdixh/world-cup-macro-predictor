"""Tests for src.imf_fetcher — IMF WEO DataMapper API client.

All tests mock ``requests.get`` and ``time.sleep`` so no real network calls
are made.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.country_map import COUNTRY_MAP
from src.imf_fetcher import fetch_imf_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(indicator: str, country_data: dict) -> dict:
    """Build a mock IMF DataMapper JSON body."""
    return {"values": {indicator: country_data}}


def _mock_get_side_effect(responses: list[dict | Exception]):
    """Return a side-effect callable for ``requests.get``."""
    idx = [0]

    def side_effect(*args, **kwargs):
        item = responses[idx[0]]
        idx[0] += 1
        if isinstance(item, Exception):
            raise item
        m = MagicMock()
        m.json.return_value = item
        m.status_code = 200
        m.raise_for_status.return_value = None
        return m

    return side_effect


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_parse_valid_response(mock_get, mock_sleep):
    """Mock JSON response → correct GDP/inflation/unemp/debt/pop values extracted."""
    countries = ["USA", "FRA"]
    responses = [
        _make_response("NGDP_RPCH", {"USA": {"2026": 2.5}, "FRA": {"2026": 1.2}}),
        _make_response("PCPIPCH", {"USA": {"2026": 1.8}, "FRA": {"2026": 2.1}}),
        _make_response("LUR", {"USA": {"2026": 3.5}, "FRA": {"2026": 7.2}}),
        _make_response("GGXWDG_NGDP", {"USA": {"2026": 98.0}, "FRA": {"2026": 112.5}}),
        _make_response("LP", {"USA": {"2026": 331.0}, "FRA": {"2026": 68.0}}),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    result = fetch_imf_data(countries, year=2026)

    assert result["USA"]["gdp"] == 2.5
    assert result["USA"]["infl"] == 1.8
    assert result["USA"]["unemp"] == pytest.approx(0.035)      # 3.5 % → decimal
    assert result["USA"]["debt_gdp"] == pytest.approx(0.98)   # 98 % → ratio
    assert result["USA"]["pop"] == 331_000_000  # millions → absolute
    assert result["USA"]["source"] == "IMF WEO 2026"

    assert result["FRA"]["gdp"] == 1.2
    assert result["FRA"]["infl"] == 2.1
    assert result["FRA"]["unemp"] == pytest.approx(0.072)
    assert result["FRA"]["debt_gdp"] == pytest.approx(1.125)
    assert result["FRA"]["pop"] == 68_000_000

    assert mock_get.call_count == 5
    assert mock_sleep.call_count == 5


@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_null_value(mock_get, mock_sleep, caplog):
    """Mock response with None for one country → returned as None with warning logged."""
    countries = ["USA", "FRA"]
    responses = [
        _make_response("NGDP_RPCH", {"USA": {"2026": 2.5}, "FRA": {"2026": None}}),
        _make_response("PCPIPCH", {"USA": {"2026": 1.8}, "FRA": {"2026": 2.1}}),
        _make_response("LUR", {"USA": {"2026": 3.5}, "FRA": {"2026": 7.2}}),
        _make_response("GGXWDG_NGDP", {"USA": {"2026": 98.0}, "FRA": {"2026": 112.5}}),
        _make_response("LP", {"USA": {"2026": 331.0}, "FRA": {"2026": 68.0}}),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    with caplog.at_level(logging.WARNING):
        result = fetch_imf_data(countries, year=2026)

    assert result["FRA"]["gdp"] is None
    assert result["USA"]["gdp"] == 2.5
    assert any("FRA" in rec.message and "NGDP_RPCH" in rec.message for rec in caplog.records)


@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_http_error(mock_get, mock_sleep):
    """Mock 500 response → graceful error, returns partial data."""
    countries = ["USA", "FRA"]
    responses = [
        _make_response("NGDP_RPCH", {"USA": {"2026": 2.5}, "FRA": {"2026": 1.2}}),
        requests.exceptions.HTTPError("500 Server Error"),
        _make_response("LUR", {"USA": {"2026": 3.5}, "FRA": {"2026": 7.2}}),
        _make_response("GGXWDG_NGDP", {"USA": {"2026": 98.0}, "FRA": {"2026": 112.5}}),
        _make_response("LP", {"USA": {"2026": 331.0}, "FRA": {"2026": 68.0}}),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    result = fetch_imf_data(countries, year=2026)

    # PCPIPCH failed → inflation should be None for both countries
    assert result["USA"]["infl"] is None
    assert result["FRA"]["infl"] is None
    # Other indicators present
    assert result["USA"]["gdp"] == 2.5
    assert result["USA"]["unemp"] == pytest.approx(0.035)
    assert result["USA"]["debt_gdp"] == pytest.approx(0.98)
    assert result["USA"]["pop"] == 331_000_000


@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_48_countries(mock_get, mock_sleep):
    """Mock response with all 48 ISO3 codes → all 48 present."""
    all_iso3 = [c["iso3"] for c in COUNTRY_MAP]

    def _build_country_data(val):
        return {iso3: {"2026": val} for iso3 in all_iso3}

    responses = [
        _make_response("NGDP_RPCH", _build_country_data(2.0)),
        _make_response("PCPIPCH", _build_country_data(2.0)),
        _make_response("LUR", _build_country_data(5.0)),
        _make_response("GGXWDG_NGDP", _build_country_data(80.0)),
        _make_response("LP", _build_country_data(10.0)),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    result = fetch_imf_data(all_iso3, year=2026)

    assert len(result) == 48
    for iso3 in all_iso3:
        assert iso3 in result
        assert result[iso3]["gdp"] == 2.0
        assert result[iso3]["infl"] == 2.0
        assert result[iso3]["unemp"] == pytest.approx(0.05)
        assert result[iso3]["debt_gdp"] == pytest.approx(0.8)
        assert result[iso3]["pop"] == 10_000_000
        assert result[iso3]["source"] == "IMF WEO 2026"


@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_year_parameter(mock_get, mock_sleep):
    """Verify API URL includes correct year (periods=2026)."""
    countries = ["USA"]
    responses = [
        _make_response("NGDP_RPCH", {"USA": {"2026": 2.5}}),
        _make_response("PCPIPCH", {"USA": {"2026": 1.8}}),
        _make_response("LUR", {"USA": {"2026": 3.5}}),
        _make_response("GGXWDG_NGDP", {"USA": {"2026": 98.0}}),
        _make_response("LP", {"USA": {"2026": 331.0}}),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    fetch_imf_data(countries, year=2026)

    for call in mock_get.call_args_list:
        url = call.args[0]
        assert "periods=2026" in url


@patch("src.imf_fetcher.time.sleep")
@patch("src.imf_fetcher.requests.get")
def test_timeout(mock_get, mock_sleep):
    """Mock timeout → handles gracefully."""
    countries = ["USA", "FRA"]
    responses = [
        _make_response("NGDP_RPCH", {"USA": {"2026": 2.5}, "FRA": {"2026": 1.2}}),
        requests.exceptions.Timeout("Request timed out"),
        _make_response("LUR", {"USA": {"2026": 3.5}, "FRA": {"2026": 7.2}}),
        _make_response("GGXWDG_NGDP", {"USA": {"2026": 98.0}, "FRA": {"2026": 112.5}}),
        _make_response("LP", {"USA": {"2026": 331.0}, "FRA": {"2026": 68.0}}),
    ]
    mock_get.side_effect = _mock_get_side_effect(responses)

    result = fetch_imf_data(countries, year=2026)

    # PCPIPCH timed out → inflation None
    assert result["USA"]["infl"] is None
    assert result["FRA"]["infl"] is None
    # Rest present
    assert result["USA"]["gdp"] == 2.5
    assert result["USA"]["unemp"] == pytest.approx(0.035)
    assert result["USA"]["debt_gdp"] == pytest.approx(0.98)
    assert result["USA"]["pop"] == 331_000_000
