"""Core prediction engine.

Computes blended scores from FIFA and economic normalised values, converts
them to expected goals (xG), applies Gaussian noise, and generates match
predictions.
"""

from __future__ import annotations

import random
from typing import Any

import pandas as pd

__all__ = [
    "compute_blended_score",
    "blended_to_xg",
    "apply_noise",
    "predict_match",
    "predict_all_upcoming",
]


def compute_blended_score(norm_fifa: float, norm_econ: float) -> float:
    """Return the 50/50 blend of FIFA and economic normalised scores."""
    return 0.5 * norm_fifa + 0.5 * norm_econ


def blended_to_xg(blended: float) -> float:
    """Map a blended score in [0, 1] to expected goals in [0, 4]."""
    return blended * 4.0


def apply_noise(xg: float, seed: int | None = None) -> float:
    """Add Gaussian noise (σ = 0.3) to *xg* and clamp to [0, 4].

    Parameters
    ----------
    xg : float
        Base expected-goals value.
    seed : int, optional
        Seed for the internal ``random.Random`` instance so results are
        reproducible without polluting the global random state.

    Returns
    -------
    float
        Noisy xG clamped to the interval ``[0, 4]``.
    """
    rng = random.Random(seed)
    noisy = xg + rng.gauss(0.0, 0.3)
    return max(0.0, min(4.0, noisy))


def predict_match(
    team_a_iso3: str,
    team_b_iso3: str,
    dataset: pd.DataFrame,
    seed: int | None = None,
) -> dict[str, Any]:
    """Predict a single match between two teams.

    Parameters
    ----------
    team_a_iso3 : str
        ISO3 code for the home / first team.
    team_b_iso3 : str
        ISO3 code for the away / second team.
    dataset : pd.DataFrame
        Normalised dataset (output of ``aggregate.normalize_scores``).
        Must contain columns: ``iso3``, ``norm_fifa``, ``norm_econ``,
        ``econ_score``, ``fifa_points``.
    seed : int, optional
        Reproducibility seed forwarded to :func:`apply_noise`.

    Returns
    -------
    dict
        Prediction dictionary with keys:
        ``team_a``, ``team_b``, ``team_a_xg``, ``team_b_xg``,
        ``predicted_score``, ``team_a_blended``, ``team_b_blended``,
        ``team_a_econ``, ``team_b_econ``, ``team_a_fifa``, ``team_b_fifa``.
    """
    a_row = dataset[dataset["iso3"] == team_a_iso3]
    b_row = dataset[dataset["iso3"] == team_b_iso3]

    if a_row.empty:
        raise ValueError(f"Team {team_a_iso3!r} not found in dataset")
    if b_row.empty:
        raise ValueError(f"Team {team_b_iso3!r} not found in dataset")

    a_norm_fifa = float(a_row["norm_fifa"].iloc[0])
    a_norm_econ = float(a_row["norm_econ"].iloc[0])
    a_econ = float(a_row["econ_score"].iloc[0])
    a_fifa = float(a_row["fifa_points"].iloc[0])

    b_norm_fifa = float(b_row["norm_fifa"].iloc[0])
    b_norm_econ = float(b_row["norm_econ"].iloc[0])
    b_econ = float(b_row["econ_score"].iloc[0])
    b_fifa = float(b_row["fifa_points"].iloc[0])

    a_blended = compute_blended_score(a_norm_fifa, a_norm_econ)
    b_blended = compute_blended_score(b_norm_fifa, b_norm_econ)

    # Use a composite seed so both teams get independent noise even when
    # the caller supplies a single seed.
    if seed is not None:
        a_xg = apply_noise(blended_to_xg(a_blended), seed=seed)
        b_xg = apply_noise(blended_to_xg(b_blended), seed=seed + 1)
    else:
        a_xg = apply_noise(blended_to_xg(a_blended))
        b_xg = apply_noise(blended_to_xg(b_blended))

    predicted_score = f"{round(a_xg)}-{round(b_xg)}"

    return {
        "team_a": team_a_iso3,
        "team_b": team_b_iso3,
        "team_a_xg": a_xg,
        "team_b_xg": b_xg,
        "predicted_score": predicted_score,
        "team_a_blended": a_blended,
        "team_b_blended": b_blended,
        "team_a_econ": a_econ,
        "team_b_econ": b_econ,
        "team_a_fifa": a_fifa,
        "team_b_fifa": b_fifa,
    }


def predict_all_upcoming(
    matches: list[dict[str, Any]],
    dataset: pd.DataFrame,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """Predict every match in *matches*.

    Parameters
    ----------
    matches : list[dict]
        Each dict must contain at least ``team_a`` and ``team_b`` keys
        with ISO3 codes.
    dataset : pd.DataFrame
        Normalised dataset (see :func:`predict_match`).
    seed : int, optional
        Base reproducibility seed.  Each match receives a derived seed
        (``seed + index``) so that the full list is deterministic.

    Returns
    -------
    list[dict]
        One prediction dict per input match, in the same order.
    """
    predictions: list[dict[str, Any]] = []
    for idx, match in enumerate(matches):
        match_seed = seed + idx if seed is not None else None
        pred = predict_match(
            match["team_a"],
            match["team_b"],
            dataset,
            seed=match_seed,
        )
        predictions.append(pred)
    return predictions
