"""Market-specific probability calculators (DNB, Asian Handicap)."""

from __future__ import annotations

from src.betting.probabilities import match_outcome_probs

__all__ = ["dnb_probs", "asian_handicap_probs"]


def dnb_probs(
    xg_home: float,
    xg_away: float,
    max_goals: int = 10,
    rho: float = 0.0,
) -> dict[str, float]:
    """Draw No Bet probabilities.

    P(home wins | no draw) = p_home / (p_home + p_away)
    P(away wins | no draw) = p_away / (p_home + p_away)

    Parameters
    ----------
    xg_home, xg_away : float
        Expected goals for each team.
    max_goals : int, default 10
        Max goals for the Poisson grid.
    rho : float, default 0.0
        Dixon-Coles correlation parameter.

    Returns
    -------
    dict
        {"home": p, "away": p} — sums to 1.0
    """
    _ = rho
    probs = match_outcome_probs(xg_home, xg_away, max_goals=max_goals)
    non_draw = probs["home"] + probs["away"]
    if non_draw <= 0.0:
        return {"home": 0.5, "away": 0.5}
    return {
        "home": probs["home"] / non_draw,
        "away": probs["away"] / non_draw,
    }


def asian_handicap_probs(
    xg_home: float,
    xg_away: float,
    line: float = -0.5,
    max_goals: int = 10,
    rho: float = 0.0,
) -> dict[str, float]:
    """Asian Handicap probabilities for half-goal lines.

    Parameters
    ----------
    xg_home, xg_away : float
        Expected goals.
    line : float, default -0.5
        Handicap line. Only -0.5 and +0.5 are supported in this MVP.
    max_goals : int, default 10
        Max goals for Poisson grid.
    rho : float, default 0.0
        Dixon-Coles correlation parameter.

    Returns
    -------
    dict
        {"home": p_home_covers, "away": p_away_covers}
    """
    _ = rho
    if line not in (-0.5, 0.5):
        raise ValueError("Only -0.5 and +0.5 Asian handicap lines are supported")

    probs = match_outcome_probs(xg_home, xg_away, max_goals=max_goals)

    if line == -0.5:
        home = probs["home"]
        away = probs["draw"] + probs["away"]
    else:
        home = probs["home"] + probs["draw"]
        away = probs["away"]

    return {"home": home, "away": away}
