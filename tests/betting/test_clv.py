from __future__ import annotations

import pytest

from src.betting.clv import clv_summary, compute_clv


def test_compute_clv_positive() -> None:
    clv = compute_clv(2.20, 1.95)
    assert clv > 0
    assert clv == pytest.approx((2.20 - 1.95) / 2.20)


def test_compute_clv_negative() -> None:
    clv = compute_clv(1.90, 2.10)
    assert clv < 0
    assert clv == pytest.approx((1.90 - 2.10) / 1.90)


def test_clv_summary_basic() -> None:
    bets = [
        {"odds_taken": 2.20, "closing_odds": 1.95},
        {"odds_taken": 1.80, "closing_odds": 1.85},
        {"odds_taken": 3.50, "closing_odds": None},
    ]

    summary = clv_summary(bets)

    expected_mean = (
        compute_clv(2.20, 1.95) + compute_clv(1.80, 1.85) + compute_clv(3.50, None)
    ) / 3

    assert summary["total_bets"] == 3
    assert summary["bets_with_closing"] == 2
    assert summary["mean_clv"] == pytest.approx(expected_mean)
