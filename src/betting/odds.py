"""Odds data ingestion and overround removal for the betting pipeline."""

from __future__ import annotations

import csv
from pathlib import Path
from collections import defaultdict
from typing import Any, Protocol

__all__ = [
    "OddsProvider",
    "CsvOddsProvider",
    "validate_odds_csv",
    "remove_overround",
    "market_implied_probs",
]


class OddsProvider(Protocol):
    """Protocol for odds data providers."""

    def fetch_odds(self) -> list[dict[str, Any]]:
        ...


class CsvOddsProvider:
    """Reads odds from a manually-exported CSV file (Bet365, etc.)."""

    REQUIRED_COLUMNS = [
        "timestamp",
        "event_id",
        "kickoff",
        "home",
        "away",
        "book",
        "market",
        "selection",
        "line",
        "decimal_odds",
    ]

    def __init__(self, csv_path: str | Path) -> None:
        self.csv_path = Path(csv_path)

    def fetch_odds(self) -> list[dict[str, Any]]:
        """Read and return the odds CSV as a list of dicts."""
        validate_odds_csv(self.csv_path)

        with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows: list[dict[str, Any]] = []
            for row in reader:
                item = dict(row)
                item["decimal_odds"] = float(item["decimal_odds"])
                rows.append(item)
        return rows


def validate_odds_csv(csv_path: str | Path) -> None:
    """Validate an odds CSV file and raise all detected errors at once."""
    path = Path(csv_path)
    errors: list[str] = []

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV file is empty or missing a header row")

            missing_columns = [
                column for column in CsvOddsProvider.REQUIRED_COLUMNS if column not in fieldnames
            ]
            if missing_columns:
                errors.append("Missing required columns: " + ", ".join(missing_columns))

            for row_number, row in enumerate(reader, start=2):
                raw_odds = (row.get("decimal_odds") or "").strip()
                if not raw_odds:
                    errors.append(f"Row {row_number}: missing decimal_odds")
                    continue

                try:
                    odds = float(raw_odds)
                except ValueError:
                    errors.append(
                        f"Row {row_number}: invalid decimal_odds {raw_odds!r} (must be a float > 1.01)"
                    )
                    continue

                if odds <= 1.01:
                    errors.append(
                        f"Row {row_number}: invalid decimal_odds {odds!r} (must be a float > 1.01)"
                    )
    except FileNotFoundError:
        raise

    if errors:
        raise ValueError("\n".join(errors))


def remove_overround(odds_by_selection: dict[str, float]) -> dict[str, float]:
    """Remove bookmaker overround (vig) from a set of decimal odds.

    Uses proportional normalization:
      raw_implied_prob_i = 1 / odds_i
      total_overround = sum(raw_implied_prob_i)
      no_vig_prob_i = raw_implied_prob_i / total_overround

    Parameters
    ----------
    odds_by_selection : dict[str, float]
        Maps selection name to decimal odds.
        E.g., {"home": 2.10, "draw": 3.40, "away": 3.60}

    Returns
    -------
    dict[str, float]
        Same keys, values are normalized implied probabilities that sum to 1.0.

    Raises
    ------
    ValueError
        If any odds ≤ 1.0, or if normalized sum deviates from 1.0 by more than 0.0001.
    """

    if not odds_by_selection:
        raise ValueError("odds_by_selection must not be empty")

    raw_implied_probs: dict[str, float] = {}
    for selection, odds in odds_by_selection.items():
        if odds <= 1.0:
            raise ValueError(f"Invalid odds for {selection!r}: {odds!r} (must be > 1.0)")
        raw_implied_probs[selection] = 1.0 / odds

    total_overround = sum(raw_implied_probs.values())
    no_vig_probs = {
        selection: raw_prob / total_overround for selection, raw_prob in raw_implied_probs.items()
    }

    normalized_sum = sum(no_vig_probs.values())
    if abs(normalized_sum - 1.0) > 0.0001:
        raise ValueError(
            f"Normalized probabilities must sum to 1.0; got {normalized_sum:.6f}"
        )

    return no_vig_probs


def market_implied_probs(
    odds_rows: list[dict], market: str = "1X2"
) -> dict[str, dict[str, float]]:
    """Group odds rows by event and return no-vig probabilities.

    Parameters
    ----------
    odds_rows : list[dict]
        Raw odds data from CsvOddsProvider.fetch_odds().
    market : str, default "1X2"
        Market to filter by.

    Returns
    -------
    dict[str, dict[str, float]]
        Maps event_id -> {selection: no_vig_probability}
    """

    grouped_odds: dict[str, dict[str, float]] = defaultdict(dict)
    for row in odds_rows:
        if row.get("market") != market:
            continue
        event_id = row["event_id"]
        selection = row["selection"]
        grouped_odds[event_id][selection] = float(row["decimal_odds"])

    return {
        event_id: remove_overround(selection_odds)
        for event_id, selection_odds in grouped_odds.items()
    }
