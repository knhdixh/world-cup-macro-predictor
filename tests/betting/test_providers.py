from __future__ import annotations

from pathlib import Path

import pytest

from src.betting.providers import OddsProviderRegistry


def test_csv_method(tmp_path: Path) -> None:
    csv_path = tmp_path / "odds.csv"
    csv_path.write_text(
        "timestamp,event_id,kickoff,home,away,book,market,selection,line,decimal_odds\n"
        "2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Spain,,1.22\n"
        "2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Draw,,5.50\n",
        encoding="utf-8",
    )

    registry = OddsProviderRegistry(csv_path=csv_path)
    odds = registry.get_odds(method="csv")

    assert len(odds) == 2
    assert odds[0]["home"] == "Spain"
    assert odds[0]["decimal_odds"] == pytest.approx(1.22)


def test_csv_missing_path() -> None:
    registry = OddsProviderRegistry()

    with pytest.raises(ValueError, match="csv_path must be set to use method='csv'"):
        registry.get_odds(method="csv")
