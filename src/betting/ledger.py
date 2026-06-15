"""Append-only paper bet ledger (CSV)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


LEDGER_COLUMNS = [
    "timestamp",
    "event_id",
    "match_date",
    "team_a",
    "team_b",
    "market",
    "selection",
    "model_prob",
    "implied_prob",
    "decimal_odds",
    "edge",
    "ev",
    "kelly",
    "stake",
    "bankroll_before",
    "bankroll_after",
    "status",
]


def init_ledger(output_path: str | Path) -> Path:
    """Create the ledger CSV with a header row if it doesn't exist."""
    path = Path(output_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
            writer.writeheader()
    return path


def log_bet(output_path: str | Path, bet: dict[str, Any], bankroll: float) -> float:
    """Log a single bet to the ledger, returning the updated bankroll."""
    path = init_ledger(output_path)
    row = {col: bet.get(col, "") for col in LEDGER_COLUMNS}
    row["status"] = bet.get("status", "candidate")
    row["bankroll_before"] = bankroll
    stake = float(bet.get("stake", 0))
    row["bankroll_after"] = round(bankroll - stake, 2)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        writer.writerow(row)

    return row["bankroll_after"]


def log_bets(output_path: str | Path, bets: list[dict[str, Any]], bankroll: float) -> float:
    """Log multiple bets sequentially and return the final bankroll."""
    current = bankroll
    for bet in bets:
        current = log_bet(output_path, bet, current)
    return current


def read_ledger(output_path: str | Path) -> list[dict[str, Any]]:
    """Read the entire ledger back as a list of dicts."""
    path = Path(output_path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
