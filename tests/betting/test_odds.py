from __future__ import annotations

from pathlib import Path

import pytest

from src.betting.odds import CsvOddsProvider, market_implied_probs, remove_overround, validate_odds_csv


def test_parse_valid_csv() -> None:
    provider = CsvOddsProvider("tests/fixtures/sample_odds.csv")

    odds = provider.fetch_odds()

    assert len(odds) == 15
    assert all(k in odds[0] for k in ["home", "away", "decimal_odds"])
    assert isinstance(odds[0]["decimal_odds"], float)


def test_missing_header() -> None:
    with pytest.raises(ValueError, match=r"Missing required columns: home"):
        validate_odds_csv("tests/fixtures/sample_odds_invalid.csv")


def test_invalid_odds_value(tmp_path: Path) -> None:
    csv_path = tmp_path / "bad_odds.csv"
    csv_path.write_text(
        "timestamp,event_id,kickoff,home,away,book,market,selection,line,decimal_odds\n"
        "2026-06-15T12:00:00,WC2026-19,2026-06-17T18:00:00,Spain,France,bet365,1X2,Spain,,1.80\n"
        "2026-06-15T12:00:00,WC2026-19,2026-06-17T18:00:00,Spain,France,bet365,1X2,Draw,,-1.50\n"
        "2026-06-15T12:00:00,WC2026-19,2026-06-17T18:00:00,Spain,France,bet365,1X2,France,,1.00\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as excinfo:
        validate_odds_csv(csv_path)

    message = str(excinfo.value)
    assert "Row 3" in message
    assert "Row 4" in message
    assert "must be a float > 1.01" in message


def test_encoding_utf8(tmp_path: Path) -> None:
    csv_path = tmp_path / "utf8_odds.csv"
    csv_path.write_text(
        "timestamp,event_id,kickoff,home,away,book,market,selection,line,decimal_odds\n"
        "2026-06-15T12:00:00,WC2026-20,2026-06-17T18:00:00,Côte d'Ivoire,Türkiye,bet365,1X2,Côte d'Ivoire,,2.10\n"
        "2026-06-15T12:00:00,WC2026-20,2026-06-17T18:00:00,Côte d'Ivoire,Türkiye,bet365,1X2,Draw,,3.30\n"
        "2026-06-15T12:00:00,WC2026-20,2026-06-17T18:00:00,Côte d'Ivoire,Türkiye,bet365,1X2,Türkiye,,3.80\n",
        encoding="utf-8",
    )

    provider = CsvOddsProvider(csv_path)
    odds = provider.fetch_odds()

    assert len(odds) == 3
    assert odds[0]["home"] == "Côte d'Ivoire"
    assert odds[0]["away"] == "Türkiye"


def test_empty_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV file is empty or missing a header row"):
        validate_odds_csv(csv_path)


def test_remove_overround_1x2() -> None:
    probs = remove_overround({"home": 2.0, "draw": 3.5, "away": 4.0})

    assert abs(sum(probs.values()) - 1.0) < 0.0001
    assert probs["home"] > probs["draw"] > probs["away"]

    grouped = market_implied_probs(
        [
            {"event_id": "WC2026-13", "market": "1X2", "selection": "home", "decimal_odds": 2.0},
            {"event_id": "WC2026-13", "market": "1X2", "selection": "draw", "decimal_odds": 3.5},
            {"event_id": "WC2026-13", "market": "1X2", "selection": "away", "decimal_odds": 4.0},
            {"event_id": "WC2026-13", "market": "OU", "selection": "over", "decimal_odds": 1.9},
        ]
    )

    assert set(grouped) == {"WC2026-13"}
    assert abs(sum(grouped["WC2026-13"].values()) - 1.0) < 0.0001
    assert set(grouped["WC2026-13"]) == {"home", "draw", "away"}


def test_remove_overround_no_overround() -> None:
    probs = remove_overround({"home": 2.0, "away": 2.0})

    assert probs == pytest.approx({"home": 0.5, "away": 0.5})


def test_remove_overround_heavy_margin() -> None:
    probs = remove_overround({"home": 1.5, "draw": 3.0, "away": 6.0})

    assert abs(sum(probs.values()) - 1.0) < 0.0001
