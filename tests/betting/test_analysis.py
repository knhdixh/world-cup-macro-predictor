from __future__ import annotations

import pytest

from src.betting.analysis import market_roi_matrix, odds_bucket_roi


def test_odds_bucket_roi_basic() -> None:
    results = [
        {"decimal_odds": 1.40, "profit": -1.0, "stake": 1.0},
        {"decimal_odds": 1.80, "profit": 0.8, "stake": 1.0},
        {"decimal_odds": 2.50, "profit": 1.5, "stake": 1.0},
        {"decimal_odds": 1.70, "profit": -1.0, "stake": 1.0},
    ]

    buckets = odds_bucket_roi(results)

    assert list(buckets.keys()) == ["1.01-1.50", "1.50-2.00", "2.00-3.00"]
    assert buckets["1.01-1.50"]["bets"] == 1.0
    assert buckets["1.01-1.50"]["total_profit"] == -1.0
    assert buckets["1.01-1.50"]["roi"] == pytest.approx(-1.0)
    assert buckets["1.50-2.00"]["bets"] == 2.0
    assert buckets["1.50-2.00"]["total_profit"] == pytest.approx(-0.2)
    assert buckets["1.50-2.00"]["roi"] == pytest.approx(-0.1)
    assert buckets["1.50-2.00"]["win_rate"] == pytest.approx(0.5)


def test_market_roi_matrix_basic() -> None:
    results = [
        {"market": "1X2", "profit": 1.0, "stake": 2.0},
        {"market": "1X2", "profit": -1.0, "stake": 1.0},
        {"market": "BTTS", "profit": 0.5, "stake": 1.0},
    ]

    matrix = market_roi_matrix(results)

    assert list(matrix.keys()) == ["1X2", "BTTS"]
    assert matrix["1X2"]["bets"] == 2.0
    assert matrix["1X2"]["total_stake"] == 3.0
    assert matrix["1X2"]["total_profit"] == 0.0
    assert matrix["1X2"]["roi"] == pytest.approx(0.0)
    assert matrix["BTTS"]["bets"] == 1.0
    assert matrix["BTTS"]["roi"] == pytest.approx(0.5)
