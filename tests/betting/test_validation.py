from __future__ import annotations

import pytest

from src.betting.validation import resolve_team_name, validate_odds_row, validate_team_pair


def test_resolve_england() -> None:
    assert resolve_team_name("England") == "GBR"


def test_resolve_ivory_coast() -> None:
    assert resolve_team_name("Ivory Coast") == "CIV"


def test_resolve_cote_divoire() -> None:
    assert resolve_team_name("Côte d'Ivoire") == "CIV"


def test_resolve_unknown_team() -> None:
    with pytest.raises(ValueError, match="Atlantis FC"):
        resolve_team_name("Atlantis FC")


def test_validate_odds_valid() -> None:
    row = {
        "home": "France",
        "away": "Brazil",
        "decimal_odds": "1.75",
        "market": "match_winner",
        "selection": "France",
    }

    assert validate_odds_row(row) == []


def test_validate_odds_invalid() -> None:
    row = {
        "home": "France",
        "away": "Brazil",
        "decimal_odds": "0",
        "market": "match_winner",
    }

    errors = validate_odds_row(row)

    assert len(errors) >= 2
    assert any("selection" in error.lower() for error in errors)
    assert any("decimal_odds" in error.lower() or "odds" in error.lower() for error in errors)
