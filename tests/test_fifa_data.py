"""Tests for src.fifa_data module.

Validates the hardcoded FIFA April 1, 2026 ranking points for all 48
World Cup 2026 nations.
"""

import pytest

from src.fifa_data import FIFA_DATA


def test_48_nations():
    """FIFA_DATA must contain exactly 48 World Cup 2026 nations."""
    assert len(FIFA_DATA) == 48


def test_france_top():
    """France (FRA) should be the top-ranked nation at ~1877.32 points."""
    assert FIFA_DATA["FRA"] == pytest.approx(1877.32, 0.01)


def test_nz_bottom():
    """New Zealand (NZL) should be the lowest-ranked at ~1281.57 points."""
    assert FIFA_DATA["NZL"] == pytest.approx(1281.57, 0.01)


def test_all_positive():
    """All FIFA ranking points must be > 1000 (FIFA uses >0, but we tighten)."""
    for iso3, points in FIFA_DATA.items():
        assert points > 1000, f"{iso3} has points={points} which is not > 1000"


def test_cross_ref_country_map():
    """Every ISO3 key in FIFA_DATA must also exist in country_map (if available)."""
    country_map = pytest.importorskip("src.country_map")
    from src.country_map import COUNTRY_MAP

    # Build a set of ISO3 codes from COUNTRY_MAP (which is list of dicts)
    map_iso3 = {entry["iso3"] for entry in COUNTRY_MAP}
    missing = [k for k in FIFA_DATA if k not in map_iso3]
    assert missing == [], f"ISO3 codes missing from COUNTRY_MAP: {missing}"


def test_no_excluded_nations():
    """Italy, Denmark, and Nigeria did NOT qualify for World Cup 2026."""
    excluded = {"ITA", "DNK", "NGA"}
    overlap = excluded & set(FIFA_DATA.keys())
    assert overlap == set(), f"Excluded (non-qualified) nations found: {overlap}"


def test_iso3_keys_are_three_chars():
    """Every key must be a 3-character uppercase ISO 3166-1 alpha-3 code."""
    for key in FIFA_DATA.keys():
        assert isinstance(key, str)
        assert len(key) == 3
        assert key.isalpha()
        assert key.isupper()


def test_ranking_points_are_floats():
    """All ranking values must be floats (decimals)."""
    for iso3, points in FIFA_DATA.items():
        assert isinstance(points, float), f"{iso3}={points!r} is not a float"
