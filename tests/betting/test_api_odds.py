"""Tests for ApiOddsProvider."""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.betting.api_odds import ApiOddsProvider


# ---------------------------------------------------------------------------
# Fixtures – sample API responses
# ---------------------------------------------------------------------------

def _sample_event(event_id: str, home: str, away: str) -> dict[str, Any]:
    """Build a single event with 3 bookmakers × 1 market × 2 outcomes."""
    return {
        "id": event_id,
        "sport_key": "soccer_world_cup",
        "commence_time": "2026-06-15T18:00:00Z",
        "home_team": home,
        "away_team": away,
        "bookmakers": [
            {
                "title": f"Book{b}",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": home, "price": 1.20 + b * 0.01},
                            {"name": away, "price": 8.00 + b * 0.10},
                        ],
                    }
                ],
            }
            for b in range(1, 4)  # 3 bookmakers
        ],
    }


@pytest.fixture
def sample_api_response() -> list[dict[str, Any]]:
    """2 events × 3 bookmakers × 1 market × 2 outcomes = 12 rows."""
    return [
        _sample_event("evt_001", "Spain", "Cabo Verde"),
        _sample_event("evt_002", "Belgium", "Egypt"),
    ]


# ---------------------------------------------------------------------------
# Helpers – mock urllib.request.urlopen
# ---------------------------------------------------------------------------

def _mock_urlopen(payload: list | dict) -> MagicMock:
    """Return a MagicMock that replaces ``urllib.request.urlopen``.

    The mock returns a context manager whose ``read().decode()`` yields the
    *payload* serialised as JSON.
    """
    response_bytes = json.dumps(payload).encode()

    mock_response = MagicMock()
    mock_response.read.return_value = response_bytes

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.__enter__.return_value = mock_response

    return mock_urlopen


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestApiOddsProvider:
    """Suite for ApiOddsProvider."""

    # -- happy path ---------------------------------------------------------

    @patch("src.betting.api_odds.urlopen")
    def test_fetch_returns_rows(
        self, mock_urlopen: MagicMock, sample_api_response: list[dict[str, Any]]
    ) -> None:
        """A valid API response is transformed into the correct number of rows."""
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(sample_api_response).encode()
        )

        provider = ApiOddsProvider(api_key="test_key_123")
        rows = provider.fetch_odds()

        # 2 events × 3 bookmakers × 1 market × 2 outcomes = 12
        assert len(rows) == 12

    # -- schema check -------------------------------------------------------

    @patch("src.betting.api_odds.urlopen")
    def test_fetch_schema(
        self, mock_urlopen: MagicMock, sample_api_response: list[dict[str, Any]]
    ) -> None:
        """Each returned row contains all required Phase-1 CSV columns."""
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps(sample_api_response).encode()
        )

        provider = ApiOddsProvider(api_key="test_key_123")
        rows = provider.fetch_odds()

        expected_keys = {
            "timestamp",
            "event_id",
            "kickoff",
            "home",
            "away",
            "book",
            "market",
            "selection",
            "line",
            "decimal_odds",
        }
        for row in rows:
            assert set(row.keys()) == expected_keys, f"Row keys mismatch: {row}"

    # -- missing API key ----------------------------------------------------

    def test_fetch_missing_api_key(self) -> None:
        """Constructor raises ValueError when no API key is available."""
        # Ensure the env var is absent for this test
        if "ODDS_API_KEY" in os.environ:
            key_backup = os.environ.pop("ODDS_API_KEY")
            restore = True
        else:
            key_backup = None
            restore = False

        try:
            with pytest.raises(ValueError, match="ODDS_API_KEY not set"):
                ApiOddsProvider(api_key=None)
        finally:
            if restore and key_backup is not None:
                os.environ["ODDS_API_KEY"] = key_backup

    # -- empty response -----------------------------------------------------

    @patch("src.betting.api_odds.urlopen")
    def test_fetch_empty_response(self, mock_urlopen: MagicMock) -> None:
        """An empty API response (``[]``) raises RuntimeError."""
        mock_urlopen.return_value.__enter__.return_value.read.return_value = (
            json.dumps([]).encode()
        )

        provider = ApiOddsProvider(api_key="test_key_123")
        with pytest.raises(RuntimeError, match="No odds data returned"):
            provider.fetch_odds()
