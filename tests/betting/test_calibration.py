from __future__ import annotations

import math

import pytest

from src.betting.calibration import (
    brier_score,
    expected_calibration_error,
    log_loss_score,
    reliability_curve,
)


def test_brier_score_perfect() -> None:
    assert brier_score([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0


def test_log_loss_golden() -> None:
    score = log_loss_score([0.5], [1])
    assert score == pytest.approx(-math.log(0.5), abs=1e-12)


def test_reliability_curve_bins() -> None:
    probs = [i / 9 for i in range(10)]
    outcomes = [1 if p >= 0.5 else 0 for p in probs]

    curve = reliability_curve(probs, outcomes, bins=10)

    assert len(curve["bin_centers"]) == 10
    assert len(curve["mean_predicted"]) == 10
    assert len(curve["mean_actual"]) == 10
    assert len(curve["counts"]) == 10
    assert sum(curve["counts"]) == 10
    assert 0.0 <= expected_calibration_error(probs, outcomes, bins=10) <= 1.0
