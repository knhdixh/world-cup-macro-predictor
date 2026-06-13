"""Tests for src/schedule.py - World Cup 2026 match schedule.

Verifies structure of 104 matches (72 group + 32 knockout) and the
get_upcoming_matches(cutoff_date) filter function.
"""

import pytest

from src.schedule import MATCHES, get_upcoming_matches


# --- Structural tests ---

def test_total_matches():
    """104 total: 72 group + 32 knockout."""
    assert len(MATCHES) == 104, f"Expected 104 matches, got {len(MATCHES)}"


def test_groups_have_6():
    """Each of 12 groups A-L has exactly 6 group-stage matches (72 total)."""
    groups = [m for m in MATCHES if m["matchday"] is not None]
    assert len(groups) == 72, f"Expected 72 group matches, got {len(groups)}"
    for letter in "ABCDEFGHIJKL":
        in_group = [m for m in groups if m["group"] == letter]
        assert len(in_group) == 6, (
            f"Group {letter} has {len(in_group)} matches, expected 6"
        )


def test_knockout_count_and_fields():
    """32 knockout matches with group=None, matchday=None, status='knockout'."""
    knockout = [m for m in MATCHES if m["status"] == "knockout"]
    assert len(knockout) == 32, f"Expected 32 knockout matches, got {len(knockout)}"
    for m in knockout:
        assert m["group"] is None
        assert m["matchday"] is None
        assert m["match_number"] >= 73
        assert m["match_number"] <= 104


def test_match_numbers_contiguous():
    """match_number covers 1..104 with no gaps and no duplicates."""
    numbers = sorted(m["match_number"] for m in MATCHES)
    assert numbers == list(range(1, 105)), (
        f"match_number must be 1..104, got first/last: "
        f"{numbers[0]}..{numbers[-1]}, unique: {len(set(numbers))}"
    )


# --- get_upcoming_matches() tests ---

def test_upcoming_filter_jun13():
    """get_upcoming_matches('2026-06-13') excludes matches #1-8 (played/today)."""
    upcoming = get_upcoming_matches("2026-06-13")
    # 104 total - 8 already played/today = 96
    assert len(upcoming) == 96, f"Expected 96 upcoming, got {len(upcoming)}"
    blocked = {1, 2, 3, 4, 5, 6, 7, 8}
    for m in upcoming:
        assert m["match_number"] not in blocked, (
            f"Match #{m['match_number']} should be excluded on 2026-06-13 cutoff"
        )


def test_upcoming_filter_jun14():
    """get_upcoming_matches('2026-06-14') returns only #9+ (MD1 only)."""
    upcoming = get_upcoming_matches("2026-06-14")
    # All 96 remaining matches (everything from #9 onwards)
    assert len(upcoming) == 96
    for m in upcoming:
        assert m["match_number"] >= 9, (
            f"Match #{m['match_number']} should be excluded on 2026-06-14 cutoff"
        )


def test_upcoming_filter_jun28():
    """get_upcoming_matches('2026-06-28') returns only knockout matches #73-104."""
    upcoming = get_upcoming_matches("2026-06-28")
    assert len(upcoming) == 32
    for m in upcoming:
        assert m["match_number"] >= 73
        assert m["status"] == "knockout"


# --- Specific match data tests ---

def test_match_36_is_1000th():
    """Match #36 is Tunisia vs Japan, group F, matchday 2, 2026-06-20."""
    m36 = next(m for m in MATCHES if m["match_number"] == 36)
    assert m36["team_a"] == "Tunisia"
    assert m36["team_b"] == "Japan"
    assert m36["group"] == "F"
    assert m36["matchday"] == 2
    assert m36["date"] == "2026-06-20"
    assert m36["status"] == "upcoming"


def test_first_eight_match_statuses():
    """Matches #1-4 are 'played', #5-8 are 'today'."""
    for n in (1, 2, 3, 4):
        m = next(m for m in MATCHES if m["match_number"] == n)
        assert m["status"] == "played", f"Match #{n} should be 'played'"
    for n in (5, 6, 7, 8):
        m = next(m for m in MATCHES if m["match_number"] == n)
        assert m["status"] == "today", f"Match #{n} should be 'today'"


# --- Country map validation (conditional - Task 2 may not be done) ---

def test_teams_in_country_map():
    """All team names are valid World Cup participants per src.country_map.COUNTRY_MAP.

    Skipped if country_map is not yet implemented (Task 2) or if the
    COUNTRY_MAP is a stub with fewer than 48 entries.
    """
    pytest.importorskip("src.country_map")
    from src.country_map import COUNTRY_MAP

    # Collect all unique team names that appear in group stage
    teams = set()
    for m in MATCHES:
        if m["matchday"] is not None:  # group stage only
            teams.add(m["team_a"])
            teams.add(m["team_b"])

    assert len(teams) == 48, (
        f"World Cup 2026 has 48 participating teams, found {len(teams)}"
    )

    valid_names: set[str] = set()
    if isinstance(COUNTRY_MAP, dict):
        valid_names = set(COUNTRY_MAP.keys())
    elif isinstance(COUNTRY_MAP, (list, tuple)):
        for entry in COUNTRY_MAP:
            if isinstance(entry, dict) and "fifa_name" in entry:
                valid_names.add(entry["fifa_name"])
            elif isinstance(entry, str):
                valid_names.add(entry)

    if len(valid_names) < 48:
        pytest.skip(
            f"COUNTRY_MAP has only {len(valid_names)} entries (stub?) — "
            "skipping team-name validation"
        )

    missing = sorted(t for t in teams if t not in valid_names)
    assert not missing, f"Teams missing from COUNTRY_MAP: {missing}"
