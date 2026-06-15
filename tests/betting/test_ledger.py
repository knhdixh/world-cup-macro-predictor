from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from src.betting.ledger import LEDGER_COLUMNS, init_ledger, log_bet, log_bets, read_ledger


def test_init_ledger() -> None:
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / "ledger.csv")

    assert path == tmp / "ledger.csv"
    assert path.exists()

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    assert rows == [LEDGER_COLUMNS]


def test_log_single_bet() -> None:
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / "ledger.csv")

    bet = {
        "timestamp": "2026-06-15",
        "event_id": "WC2026-13",
        "match_date": "2026-06-15",
        "team_a": "ESP",
        "team_b": "CPV",
        "market": "1X2",
        "selection": "ESP",
        "model_prob": 0.82,
        "implied_prob": 0.80,
        "decimal_odds": 1.25,
        "edge": 0.02,
        "ev": 0.025,
        "kelly": 0.02,
        "stake": 5.0,
        "status": "candidate",
    }

    remaining = log_bet(path, bet, 1000.0)

    assert remaining == 995.0
    rows = read_ledger(path)
    assert len(rows) == 1
    assert rows[0]["bankroll_before"] == "1000.0"
    assert rows[0]["bankroll_after"] == "995.0"
    assert rows[0]["stake"] == "5.0"


def test_log_multiple_bets() -> None:
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / "ledger.csv")

    bets = [
        {"event_id": "A", "stake": 5.0, "status": "candidate"},
        {"event_id": "B", "stake": 15.0, "status": "candidate"},
    ]

    final_bankroll = log_bets(path, bets, 1000.0)

    assert final_bankroll == 980.0
    rows = read_ledger(path)
    assert [row["event_id"] for row in rows] == ["A", "B"]
    assert [row["bankroll_before"] for row in rows] == ["1000.0", "995.0"]
    assert [row["bankroll_after"] for row in rows] == ["995.0", "980.0"]


def test_read_empty_ledger() -> None:
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / "ledger.csv")

    assert read_ledger(path) == []


def test_ledger_schema() -> None:
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / "ledger.csv")

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == LEDGER_COLUMNS

    assert len(LEDGER_COLUMNS) == 17
