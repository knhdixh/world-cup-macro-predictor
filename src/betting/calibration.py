"""Probability calibration metrics for evaluating model predictions."""

from __future__ import annotations

import math

__all__ = [
    "brier_score",
    "log_loss_score",
    "reliability_curve",
    "expected_calibration_error",
]


def _validate_inputs(probs: list[float], outcomes: list[int]) -> None:
    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must have the same length")
    if not probs:
        raise ValueError("probs and outcomes must not be empty")


def brier_score(probs: list[float], outcomes: list[int]) -> float:
    """Compute the Brier Score (mean squared error of predictions)."""
    _validate_inputs(probs, outcomes)
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def log_loss_score(probs: list[float], outcomes: list[int], eps: float = 1e-15) -> float:
    """Compute logarithmic loss (cross-entropy)."""
    _validate_inputs(probs, outcomes)
    total = 0.0
    for p, o in zip(probs, outcomes):
        p = min(max(p, eps), 1.0 - eps)
        total += o * math.log(p) + (1 - o) * math.log(1.0 - p)
    return -total / len(probs)


def reliability_curve(probs: list[float], outcomes: list[int], bins: int = 10) -> dict:
    """Compute reliability curve (calibration) for predicted probabilities."""
    _validate_inputs(probs, outcomes)
    if bins <= 0:
        raise ValueError("bins must be positive")

    counts = [0] * bins
    sum_predicted = [0.0] * bins
    sum_actual = [0.0] * bins

    for p, o in zip(probs, outcomes):
        index = min(int(p * bins), bins - 1)
        counts[index] += 1
        sum_predicted[index] += p
        sum_actual[index] += o

    bin_centers = [(i + 0.5) / bins for i in range(bins)]
    mean_predicted = [sum_predicted[i] / counts[i] if counts[i] else 0.0 for i in range(bins)]
    mean_actual = [sum_actual[i] / counts[i] if counts[i] else 0.0 for i in range(bins)]

    return {
        "bin_centers": bin_centers,
        "mean_predicted": mean_predicted,
        "mean_actual": mean_actual,
        "counts": counts,
    }


def expected_calibration_error(probs: list[float], outcomes: list[int], bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE)."""
    curve = reliability_curve(probs, outcomes, bins=bins)
    total = len(probs)
    return sum(
        (count / total) * abs(mp - ma)
        for count, mp, ma in zip(curve["counts"], curve["mean_predicted"], curve["mean_actual"])
        if count
    )
