"""Tests for src.bis_fetcher module.

Validates BIS central bank policy rate fetching via SDMX API using mocks.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src import bis_fetcher


# Sample BIS XML response for a valid country (US rate 5.50)
_VALID_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">'
    '<message:DataSet>'
    '<Series FREQ="M" REF_AREA="US">'
    '<Obs TIME_PERIOD="2026-05" OBS_VALUE="5.50"/>'
    '</Series>'
    '</message:DataSet>'
    '</message:StructureSpecificData>'
)

# XML response with no Obs element (empty data)
_EMPTY_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<message:StructureSpecificData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">'
    '<message:DataSet>'
    '<Series FREQ="M" REF_AREA="CUW">'
    '</Series>'
    '</message:DataSet>'
    '</message:StructureSpecificData>'
)


def test_parse_valid_csv():
    """Mock BIS XML response → correct rate extracted (e.g., US ~5.5)."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = _VALID_XML

    with patch("src.bis_fetcher.requests.get", return_value=mock_response):
        result = bis_fetcher.fetch_policy_rate("US")

    assert result == pytest.approx(5.50, 0.01)


def test_missing_country():
    """BIS returns empty/error → returns None without exception."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = _EMPTY_XML

    with patch("src.bis_fetcher.requests.get", return_value=mock_response):
        result = bis_fetcher.fetch_policy_rate("CW")

    assert result is None


def test_http_404():
    """Mock 404 → returns None gracefully."""
    mock_response = Mock()
    mock_response.status_code = 404

    with patch("src.bis_fetcher.requests.get", return_value=mock_response):
        result = bis_fetcher.fetch_policy_rate("XY")

    assert result is None


def test_batch_fetch():
    """Multiple ISO3 → correct dict structure {ISO3: rate, ISO3: None, ...}."""
    def side_effect(url, **kwargs):
        mock_response = Mock()
        if "US" in url:
            mock_response.status_code = 200
            mock_response.text = _VALID_XML
        elif "CW" in url:
            mock_response.status_code = 200
            mock_response.text = _EMPTY_XML
        else:
            mock_response.status_code = 404
        return mock_response

    with (
        patch("src.bis_fetcher.requests.get", side_effect=side_effect) as get_mock,
        patch("src.bis_fetcher.time.sleep") as sleep_mock,
    ):
        countries = ["USA", "CUW", "XYZ"]
        result = bis_fetcher.fetch_all_policy_rates(countries)

    assert isinstance(result, dict)
    assert result["USA"] == pytest.approx(5.50, 0.01)
    assert result["CUW"] is None
    assert result["XYZ"] is None
    assert get_mock.call_count == 2  # XYZ has no ISO-2 mapping, so no HTTP call
    assert sleep_mock.call_count == 2  # sleep after USA and CUW (not after last item XYZ)


def test_timeout():
    """Mock timeout → returns None."""
    with patch(
        "src.bis_fetcher.requests.get",
        side_effect=bis_fetcher.requests.exceptions.Timeout,
    ):
        result = bis_fetcher.fetch_policy_rate("FR")

    assert result is None


def test_invalid_xml_format():
    """BIS returns malformed XML → returns None without crashing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "not valid xml at all <<<"

    with patch("src.bis_fetcher.requests.get", return_value=mock_response):
        result = bis_fetcher.fetch_policy_rate("DE")

    assert result is None
