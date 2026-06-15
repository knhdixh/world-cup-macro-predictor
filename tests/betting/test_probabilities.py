from __future__ import annotations

import math

import pytest

from src.betting.probabilities import (
    btts_probs,
    match_outcome_probs,
    poisson_pmf,
    poisson_probs,
    totals_probs,
    validate_tail_mass,
)


def test_poisson_pmf_sum_to_one(sample_xg_params: dict[str, float]) -> None:
    probs = poisson_probs(sample_xg_params["lam"], int(sample_xg_params["max_goals"]))
    assert abs(sum(probs) - 1.0) < 0.0001


def test_poisson_pmf_zero_k() -> None:
    assert poisson_pmf(0, 2.0) == pytest.approx(math.exp(-2.0), abs=1e-10)


def test_degenerate_low_xg() -> None:
    probs = poisson_probs(0.0)
    assert probs[0] > 0.99
    assert sum(probs) > 0.99


def test_degenerate_high_xg() -> None:
    probs = poisson_probs(4.0, 10)
    tail = 1.0 - sum(probs)
    assert tail < 0.001


def test_tail_mass_validation() -> None:
    with pytest.raises(ValueError):
        validate_tail_mass([0.2, 0.3, 0.4], threshold=0.01)


def test_negative_lam() -> None:
    probs = poisson_probs(-1.0, 10)
    assert all(not math.isnan(p) for p in probs)
    assert all(math.isfinite(p) for p in probs)
    assert probs[0] > 0.99


def test_totals_over_25() -> None:
    probs = totals_probs(2.0, 1.5)
    assert probs["over"] > probs["under"]


def test_totals_under_25() -> None:
    probs = totals_probs(0.5, 0.5)
    assert probs["under"] > probs["over"]


def test_btts_high_xg() -> None:
    probs = btts_probs(2.0, 2.0)
    assert probs["yes"] > 0.70


def test_btts_low_xg() -> None:
    probs = btts_probs(0.1, 0.1)
    assert probs["yes"] < 0.05


def test_totals_sum_to_one() -> None:
    probs = totals_probs(2.0, 1.5)
    assert abs(sum(probs.values()) - 1.0) < 0.0001


def test_1x2_golden() -> None:
    probs = match_outcome_probs(2.0, 1.0)
    assert probs["home"] > probs["draw"] > probs["away"]
    assert abs(sum(probs.values()) - 1.0) < 0.001


def test_1x2_extreme_mismatch() -> None:
    probs = match_outcome_probs(4.0, 0.0)
    assert probs["home"] > 0.95


def test_1x2_balanced() -> None:
    probs = match_outcome_probs(2.0, 2.0)
    assert abs(probs["home"] - probs["away"]) < 0.001
    assert probs["draw"] == pytest.approx(0.207, abs=0.02)


def test_1x2_prob_sum() -> None:
    probs = match_outcome_probs(1.7, 1.3)
    assert abs(sum(probs.values()) - 1.0) < 0.001
