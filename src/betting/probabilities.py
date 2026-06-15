"""Poisson probability helpers for betting xG models.

Pure math utilities for turning expected goals (xG) into a discrete goal
distribution.
"""

from __future__ import annotations

import math

__all__ = [
    "poisson_pmf",
    "poisson_probs",
    "validate_tail_mass",
    "totals_probs",
    "btts_probs",
    "match_outcome_probs",
]


def poisson_pmf(k: int, lam: float) -> float:
    """Return the Poisson probability mass for ``P(X = k)``.

    Parameters
    ----------
    k : int
        Goal count.
    lam : float
        Expected goals parameter. Non-positive values are floored.

    Returns
    -------
    float
        Probability of observing exactly ``k`` goals.
    """
    if lam <= 0:
        lam = 1e-6
    return math.exp(-lam) * (lam**k) / math.factorial(k)


def poisson_probs(lam: float, max_goals: int = 10) -> list[float]:
    """Return Poisson probabilities for goal counts from 0 through ``max_goals``.

    Parameters
    ----------
    lam : float
        Expected goals parameter. Non-positive values are floored.
    max_goals : int, default 10
        Maximum goal count to include in the returned distribution.

    Returns
    -------
    list[float]
        Probabilities for ``k = 0..max_goals``.
    """
    if lam <= 0:
        lam = 1e-6
    probs = [poisson_pmf(k, lam) for k in range(max_goals)]
    probs.append(max(0.0, 1.0 - sum(probs)))
    return probs


def validate_tail_mass(probs: list[float], threshold: float = 0.001) -> None:
    """Raise when the remaining tail mass exceeds ``threshold``.

    Parameters
    ----------
    probs : list[float]
        Truncated probability distribution.
    threshold : float, default 0.001
        Maximum allowed remaining tail mass.

    Returns
    -------
    None
        Returns normally when the tail mass is within the threshold.

    Raises
    ------
    ValueError
        If the remaining probability mass is too large.
    """
    tail = 1.0 - sum(probs)
    if tail > threshold:
        raise ValueError(f"Tail mass {tail:.6f} exceeds threshold {threshold}")


def totals_probs(
    xg_home: float,
    xg_away: float,
    line: float = 2.5,
    max_goals: int = 10,
) -> dict[str, float]:
    """Return over/under probabilities for a total goals line.

    The sum of two independent Poisson(λ₁)+Poisson(λ₂) is Poisson(λ₁+λ₂).
    So P(total = k) = poisson_pmf(k, xg_home + xg_away).
    P(over) = Σ P(total > line), P(under) = Σ P(total < line).
    For line=2.5, no push is possible since Poisson is discrete.

    Returns {"over": p, "under": p}, summing to 1.0.
    """
    if line != 2.5:
        raise ValueError("Only the 2.5 totals line is supported in this MVP")

    total_lambda = xg_home + xg_away
    probs = poisson_probs(total_lambda, max_goals=max_goals)
    under = sum(probs[:3])
    over = max(0.0, 1.0 - under)
    return {"over": over, "under": under}


def btts_probs(xg_home: float, xg_away: float) -> dict[str, float]:
    """Return both-teams-to-score probabilities.

    P(home scores ≥ 1) = 1 - e^(-xg_home)
    P(away scores ≥ 1) = 1 - e^(-xg_away)
    Independence assumption: P(BTTS yes) = P(home≥1) * P(away≥1)

    Returns {"yes": p, "no": p}, summing to 1.0.

    NOTE: This assumes independence between home and away scoring.
    Independence assumption. Low-score correlation adjustment
    deferred to Phase 2.
    """
    home_scores = 1.0 - math.exp(-max(0.0, xg_home))
    away_scores = 1.0 - math.exp(-max(0.0, xg_away))
    yes = home_scores * away_scores
    no = 1.0 - yes
    return {"yes": yes, "no": no}


def match_outcome_probs(
    xg_home: float, xg_away: float, max_goals: int = 10
) -> dict[str, float]:
    """Return home/draw/away probabilities from Poisson goal distribution.

    Builds an outer-product matrix P(home=i, away=j) = P_home(i) * P_away(j)
    for i,j in [0, max_goals], then sums:
      - p_home = sum of cells where i > j
      - p_draw = sum of cells where i == j
      - p_away = sum of cells where i < j

    Parameters
    ----------
    xg_home : float
        Expected goals for the home team.
    xg_away : float
        Expected goals for the away team.
    max_goals : int, default 10
        Maximum goals considered.

    Returns
    -------
    dict[str, float]
        Keys: "home", "draw", "away". Sums to 1.0 ± 0.0001.
    """
    home_probs = poisson_probs(xg_home, max_goals)
    away_probs = poisson_probs(xg_away, max_goals)

    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = home_probs[i] * away_probs[j]
            if i > j:
                p_home += prob
            elif i < j:
                p_away += prob
            else:
                p_draw += prob

    return {"home": p_home, "draw": p_draw, "away": p_away}
