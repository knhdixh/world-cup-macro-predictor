"""Research validator — checks bet candidates against real-world factors."""

from __future__ import annotations

import csv
from datetime import datetime, date
from pathlib import Path
from typing import Any

from src.betting.validation import resolve_team_name


class ResearchValidator:
    """Validates bet candidates against real-world research.

    Checks injuries, rest days, motivation, and other factors
    that could invalidate a model-predicted edge.

    A veto means: "the model says this is a good bet, but
    real-world factors make it too risky."
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent.parent / "data" / "research"
        self._injuries: dict[str, list[dict[str, str]]] = {}

    def load_injuries(self) -> None:
        """Load injury data from CSV.

        CSV format: team_iso3,player_name,status,date
        where status is "out", "doubtful", or "returned"
        """
        path = self.data_dir / "injuries.csv"
        if not path.exists():
            raise FileNotFoundError(f"Injury data not found: {path}")

        self._injuries.clear()
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = row["team_iso3"].strip().upper()
                self._injuries.setdefault(team, []).append({
                    "player_name": row["player_name"].strip(),
                    "status": row["status"].strip().lower(),
                    "date": row["date"].strip(),
                })

    def check_injuries(self, team_iso3: str) -> list[str]:
        """Get list of injured/doubtful players for a team.

        Returns names of players whose status is "out" or "doubtful".
        Players who have "returned" are excluded.
        """
        team = team_iso3.strip().upper()
        if team not in self._injuries:
            return []

        active: list[str] = []
        for entry in self._injuries[team]:
            if entry["status"] in ("out", "doubtful"):
                active.append(entry["player_name"])
        return active

    @staticmethod
    def check_rest_days(match_date: str, last_match_date: str | None) -> int:
        """Calculate days between matches.

        If last_match_date is None, returns a high default (14).
        Returns days of rest.
        """
        if last_match_date is None:
            return 14

        match = datetime.strptime(match_date, "%Y-%m-%d").date()
        last = datetime.strptime(last_match_date, "%Y-%m-%d").date()
        delta = (match - last).days
        return max(delta, 0)

    @staticmethod
    def check_motivation(tournament_stage: str,
                         team_qualified: bool = True,
                         team_eliminated: bool = False) -> str:
        """Assess team motivation based on tournament context.

        Returns one of: "must_win", "normal", "dead_rubber"

        A "dead_rubber" occurs when:
        - Both teams are already eliminated (neither can advance), OR
        - Both teams have already qualified (result doesn't change standings)

        A "must_win" occurs when the team is in a knockout stage
        (round_of_32 or later) and the match is single-elimination.

        Otherwise returns "normal".
        """
        if team_eliminated and not team_qualified:
            return "dead_rubber"

        knockout_stages = {"round_of_32", "round_of_16", "quarter", "semi", "final"}
        if tournament_stage in knockout_stages:
            return "must_win"

        return "normal"

    def veto_bet(self, candidate: dict[str, Any]) -> tuple[bool, str]:
        """Check if a bet candidate should be vetoed.

        Veto conditions:
        - Key player injured (any player listed as "out")
        - Less than 3 days rest
        - Dead rubber match (both teams eliminated or already qualified)

        Parameters expected in *candidate* dict:
            team_iso3           — ISO3 code of the team being bet on
            match_date          — date string in YYYY-MM-DD format
            last_match_date     — (optional) previous match date
            tournament_stage    — stage name e.g. "group", "quarter"
            team_qualified      — (optional) bool, default True
            team_eliminated     — (optional) bool, default False

        Returns (approved: bool, reason: str)
        """
        team_iso3 = candidate.get("team_iso3", "")
        match_date = candidate.get("match_date", "")
        tournament_stage = candidate.get("tournament_stage", "group")

        # --- Injury check ---
        injured = self.check_injuries(team_iso3)
        if injured:
            players = ", ".join(injured)
            return (False, f"Injury veto: {players} {'are' if len(injured) > 1 else 'is'} unavailable for {team_iso3}")

        # --- Rest days check ---
        last_match = candidate.get("last_match_date")
        rest = self.check_rest_days(match_date, last_match)
        if rest < 3 and last_match is not None:
            return (False, f"Rest veto: {team_iso3} has only {rest} day(s) of rest (minimum 3 required)")

        # --- Motivation check ---
        team_qualified = candidate.get("team_qualified", True)
        team_eliminated = candidate.get("team_eliminated", False)
        motivation = self.check_motivation(tournament_stage, team_qualified, team_eliminated)
        if motivation == "dead_rubber":
            return (False, f"Motivation veto: dead rubber match — {team_iso3} has nothing to play for")

        return (True, "")
