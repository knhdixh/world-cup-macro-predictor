"""Football team feature engineering — Elo, squad value, form."""

from __future__ import annotations

import math
from typing import Any


# Default Elo parameters
ELO_START = 1500.0
ELO_K = 32  # K-factor for World Cup matches


class EloSystem:
    """Maintain Elo ratings for international football teams."""

    def __init__(self, initial_rating: float = ELO_START) -> None:
        self.ratings: dict[str, float] = {}
        self.initial_rating = initial_rating

    def get_rating(self, team_iso3: str) -> float:
        """Get current Elo rating for a team, initializing if unknown."""
        if team_iso3 not in self.ratings:
            self.ratings[team_iso3] = self.initial_rating
        return self.ratings[team_iso3]

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Expected score for team A against team B.

        E_A = 1 / (1 + 10^((rating_B - rating_A) / 400))
        """
        exponent = (rating_b - rating_a) / 400.0
        return 1.0 / (1.0 + math.pow(10.0, exponent))

    def update_ratings(
        self,
        team_a: str,
        team_b: str,
        goals_a: int,
        goals_b: int,
        k: float = ELO_K,
    ) -> tuple[float, float]:
        """Update Elo ratings after a match.

        Result is determined by actual goals:
        - win for A: S_A = 1, S_B = 0
        - draw: S_A = 0.5, S_B = 0.5
        - win for B: S_A = 0, S_B = 1

        New rating = old rating + K * (S - E)
        """
        rating_a = self.get_rating(team_a)
        rating_b = self.get_rating(team_b)

        e_a = self.expected_score(rating_a, rating_b)
        e_b = 1.0 - e_a

        if goals_a > goals_b:
            s_a, s_b = 1.0, 0.0
        elif goals_a == goals_b:
            s_a, s_b = 0.5, 0.5
        else:
            s_a, s_b = 0.0, 1.0

        new_a = rating_a + k * (s_a - e_a)
        new_b = rating_b + k * (s_b - e_b)

        self.ratings[team_a] = new_a
        self.ratings[team_b] = new_b

        return new_a, new_b

    def to_dict(self) -> dict[str, float]:
        """Return copy of all ratings."""
        return dict(self.ratings)


def compute_elo_features(
    team_a: str,
    team_b: str,
    elo_system: EloSystem,
) -> dict[str, float]:
    """Compute Elo-based features for a match.

    Returns:
      elo_a: team A's current Elo
      elo_b: team B's current Elo
      elo_diff: elo_a - elo_b
      elo_win_prob_a: expected score for A (win probability)
    """
    elo_a = elo_system.get_rating(team_a)
    elo_b = elo_system.get_rating(team_b)
    elo_win_prob_a = elo_system.expected_score(elo_a, elo_b)

    return {
        "elo_a": elo_a,
        "elo_b": elo_b,
        "elo_diff": elo_a - elo_b,
        "elo_win_prob_a": elo_win_prob_a,
    }


def squad_value_features(
    team_a: str,
    team_b: str,
    squad_values: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute squad market value features.

    If squad_values is None, returns placeholder features using
    FIFA ranking points as proxy.

    Returns:
      value_a, value_b, value_ratio, value_diff
    """
    # TODO: Use real Transfermarkt squad values when available.
    # For now, use FIFA ranking points as a proxy.
    if squad_values is None:
        squad_values = _fifa_ranking_proxy()

    value_a = squad_values.get(team_a, 0.0)
    value_b = squad_values.get(team_b, 0.0)

    if value_b > 0 and value_a > 0:
        value_ratio = value_a / value_b
    elif value_a > 0:
        value_ratio = 10.0
    else:
        value_ratio = 0.1

    return {
        "value_a": value_a,
        "value_b": value_b,
        "value_ratio": value_ratio,
        "value_diff": value_a - value_b,
    }


def _fifa_ranking_proxy() -> dict[str, float]:
    """Return a dummy FIFA ranking score mapping as proxy for squad values.

    These are illustrative values, not real FIFA points.
    """
    # fmt: off
    return {
        "ARG": 1835.4, "FRA": 1832.6, "BRA": 1812.3, "BEL": 1798.1,
        "GBR": 1775.5, "PRT": 1762.8, "NLD": 1758.9, "ESP": 1752.1,
        "HRV": 1745.3, "DEU": 1739.7, "ITA": 1730.2, "MAR": 1725.6,
        "URY": 1721.0, "CHE": 1715.4, "COL": 1712.8, "MEX": 1705.3,
        "SEN": 1698.7, "DEU": 1739.7, "JPN": 1688.2, "KOR": 1675.5,
        "SWE": 1670.1, "AUT": 1662.4, "TUR": 1658.9, "CZE": 1645.3,
        "USA": 1640.8, "AUS": 1632.5, "ECU": 1625.1, "CAN": 1618.7,
        "NOR": 1612.3, "IRN": 1605.8, "DZA": 1598.4, "CIV": 1592.6,
        "EGY": 1585.2, "TUN": 1578.5, "SAU": 1570.9, "COD": 1565.3,
        "GHA": 1558.7, "BIH": 1552.1, "PRY": 1545.5, "JOR": 1538.9,
        "IRQ": 1532.3, "UZB": 1525.8, "HTI": 1518.5, "PAN": 1512.3,
        "CPV": 1505.7, "CUW": 1498.5, "NZL": 1492.1, "ZAF": 1485.7,
        "QAT": 1478.5, "SCO": 1472.3, "KOR": 1465.8,
    }
    # fmt: on


def form_features(
    team_a: str,
    team_b: str,
    recent_results: dict[str, list[int]] | None = None,
) -> dict[str, float]:
    """Compute recent form features.

    recent_results format: {team_iso3: [1, 1, 0, -1, 1]} where
    1=win, 0=draw, -1=loss (most recent first)

    Returns:
      form_a, form_b, form_diff — average points per match over last 5
    """
    if recent_results is None:
        return {
            "form_a": 0.0,
            "form_b": 0.0,
            "form_diff": 0.0,
        }

    def _avg_form(results: list[int]) -> float:
        """Convert results list to average points per match (last 5)."""
        last5 = results[:5]
        if not last5:
            return 0.0
        # Map: win=1 -> 3pts, draw=0 -> 1pt, loss=-1 -> 0pt
        total = 0
        for r in last5:
            if r == 1:
                total += 3
            elif r == 0:
                total += 1
            # r == -1 contributes 0
        return total / len(last5)

    form_a = _avg_form(recent_results.get(team_a, []))
    form_b = _avg_form(recent_results.get(team_b, []))

    return {
        "form_a": form_a,
        "form_b": form_b,
        "form_diff": form_a - form_b,
    }
