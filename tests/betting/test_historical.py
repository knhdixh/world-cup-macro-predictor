"""Tests for src.betting.historical — HistoricalDB."""

from src.betting.historical import HistoricalDB


def test_load_all_tournaments() -> None:
    """Load all 4 tournaments, verify total 192 group-stage matches."""
    db = HistoricalDB()
    all_matches = db.get_all_matches()
    assert len(all_matches) == 192, (
        f"Expected 192 matches across 4 tournaments, got {len(all_matches)}"
    )


def test_load_single_tournament() -> None:
    """Load 2014 only, verify 48 group-stage matches."""
    db = HistoricalDB()
    matches_2014 = db.load_fixtures(2014)
    assert len(matches_2014) == 48, (
        f"Expected 48 matches for 2014, got {len(matches_2014)}"
    )
    for m in matches_2014:
        assert m["tournament"] == 2014


def test_real_result_present() -> None:
    """Load 2022, verify Argentina 1-2 Saudi Arabia exists."""
    db = HistoricalDB()
    matches_2022 = db.load_fixtures(2022)
    # Match #13: Argentina vs Saudi Arabia, 1-2
    match_13 = next(
        (m for m in matches_2022 if m["match_number"] == 13), None
    )
    assert match_13 is not None, "Match #13 not found in 2022 fixtures"
    assert match_13["team_a"] == "ARG", (
        f"Expected ARG as team_a, got {match_13['team_a']}"
    )
    assert match_13["team_b"] == "SAU", (
        f"Expected SAU as team_b, got {match_13['team_b']}"
    )
    assert match_13["team_a_goals"] == 1
    assert match_13["team_b_goals"] == 2
