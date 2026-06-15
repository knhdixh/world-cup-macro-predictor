"""Historical match database for backtesting."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class HistoricalDB:
    """Loads and queries historical World Cup match data."""

    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "historical"

    TOURNAMENTS = [2010, 2014, 2018, 2022]

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else self.DATA_DIR

    def load_fixtures(self, tournament: int | None = None) -> list[dict[str, Any]]:
        """Load match fixtures for given tournament (or all if None).

        Returns list of dicts with keys:
            tournament, match_number, date, team_a, team_b,
            team_a_goals, team_b_goals, team_a_fifa, team_b_fifa,
            odds_home, odds_draw, odds_away
        """
        years = [tournament] if tournament else self.TOURNAMENTS
        matches: list[dict[str, Any]] = []

        for year in years:
            path = self.data_dir / f"fixtures_{year}.csv"
            if not path.exists():
                raise FileNotFoundError(
                    f"Fixture file not found: {path}"
                )
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    matches.append({
                        "tournament": int(row["tournament"]),
                        "match_number": int(row["match_number"]),
                        "date": row["date"],
                        "team_a": row["team_a"],
                        "team_b": row["team_b"],
                        "team_a_goals": int(row["team_a_goals"]),
                        "team_b_goals": int(row["team_b_goals"]),
                        "team_a_fifa": float(row["team_a_fifa"]),
                        "team_b_fifa": float(row["team_b_fifa"]),
                        "odds_home": float(row["odds_home"]),
                        "odds_draw": float(row["odds_draw"]),
                        "odds_away": float(row["odds_away"]),
                    })

        return matches

    def load_rankings(self, tournament: int) -> dict[str, float]:
        """Load FIFA ranking snapshot for a tournament year.

        Returns dict mapping ISO3 -> ranking points.
        """
        path = self.data_dir / f"fifa_rankings_{tournament}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Rankings file not found: {path}"
            )
        rankings: dict[str, float] = {}
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rankings[row["team"]] = float(row["fifa_points"])
        return rankings

    def get_all_matches(self) -> list[dict[str, Any]]:
        """Return all loaded matches from all tournaments."""
        return self.load_fixtures()
