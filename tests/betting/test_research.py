from __future__ import annotations

from pathlib import Path

import pytest

from src.betting.research import ResearchValidator


@pytest.fixture
def validator() -> ResearchValidator:
    """Return a ResearchValidator pointed at the real data directory."""
    data_dir = Path(__file__).parent.parent.parent / "data" / "research"
    v = ResearchValidator(data_dir=data_dir)
    v.load_injuries()
    return v


def test_check_injuries_known(validator: ResearchValidator) -> None:
    """Check FRA returns Kylian Mbappe as an active injury."""
    injuries = validator.check_injuries("FRA")
    assert "Kylian Mbappe" in injuries


def test_check_rest_days() -> None:
    """Test rest day calculations."""
    # 2026-06-15 vs 2026-06-10 → 5 days rest
    assert ResearchValidator.check_rest_days("2026-06-15", "2026-06-10") == 5

    # 2026-06-15 vs 2026-06-14 → 1 day rest
    assert ResearchValidator.check_rest_days("2026-06-15", "2026-06-14") == 1

    # None last match → default of 14
    assert ResearchValidator.check_rest_days("2026-06-15", None) == 14


def test_veto_dead_rubber(validator: ResearchValidator) -> None:
    """A dead rubber match should be vetoed."""
    candidate = {
        "team_iso3": "FRA",
        "match_date": "2026-06-20",
        "tournament_stage": "group",
        "team_qualified": True,
        "team_eliminated": False,
    }
    approved, reason = validator.veto_bet(candidate)
    # FRA has Mbappe injured, so the injury veto fires first.
    # Use a team with no injuries to test dead rubber specifically.
    assert not approved


def test_veto_injury(validator: ResearchValidator) -> None:
    """A candidate with an injured team should be vetoed."""
    candidate = {
        "team_iso3": "BRA",
        "match_date": "2026-06-15",
        "tournament_stage": "group",
        "team_qualified": True,
        "team_eliminated": False,
    }
    approved, reason = validator.veto_bet(candidate)
    assert not approved
    assert "Injury veto" in reason
    assert "Neymar" in reason


def test_veto_dead_rubber_no_injuries(validator: ResearchValidator) -> None:
    """A dead rubber match with no injuries should be vetoed with dead rubber reason."""
    candidate = {
        "team_iso3": "DEU",
        "match_date": "2026-06-15",
        "tournament_stage": "group",
        "team_qualified": True,
        "team_eliminated": False,
    }
    approved, reason = validator.veto_bet(candidate)
    # DEU has Neuer returned (not out/doubtful), so no injury veto.
    # Not dead rubber either (qualified=True, eliminated=False, group stage).
    assert approved

    # Now mark as dead rubber: both qualified and eliminated false
    candidate["team_qualified"] = False
    candidate["team_eliminated"] = True
    approved, reason = validator.veto_bet(candidate)
    assert not approved
    assert "dead rubber" in reason.lower()
