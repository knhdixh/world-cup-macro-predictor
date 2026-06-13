"""Shared pytest fixtures for football-prediction tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_iso3_codes() -> list[str]:
    """Sample list of country ISO 3166-1 alpha-3 codes for testing.

    Includes a mix of confederations and FIFA World Cup participants.
    """
    return ["USA", "FRA", "DEU", "BRA", "ARG", "JPN", "NZL", "CUW"]


# Backwards-compatible alias (some test files may import the constant name)
SAMPLE_ISO3_CODES = ["USA", "FRA", "DEU", "BRA", "ARG", "JPN", "NZL", "CUW"]
