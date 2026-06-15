from __future__ import annotations

from src.betting.selector import (
    edge,
    expected_value,
    is_candidate,
    kelly_fraction,
    recommend_stake,
)


def test_ev_positive() -> None:
    ev = expected_value(0.40, 3.00)
    assert abs(ev - 0.20) < 0.001


def test_ev_negative() -> None:
    ev = expected_value(0.30, 2.00)
    assert abs(ev - (-0.40)) < 0.001


def test_ev_breakeven() -> None:
    ev = expected_value(0.50, 2.00)
    assert abs(ev - 0.00) < 0.001


def test_edge_percentage() -> None:
    value = edge(0.55, 0.50)
    assert abs(value - 0.05) < 0.001


def test_is_candidate_ev_below_threshold() -> None:
    assert not is_candidate(0.02, 2.00, min_ev=0.03)


def test_is_candidate_odds_outside_range() -> None:
    assert not is_candidate(0.10, 4.00, min_ev=0.03, max_odds=3.50)


def test_kelly_golden() -> None:
    quarter = kelly_fraction(0.55, 2.00)
    full = kelly_fraction(0.55, 2.00, fraction=1.0)
    assert abs(full - 0.10) < 0.001
    assert abs(quarter - 0.025) < 0.001


def test_kelly_negative_ev() -> None:
    assert kelly_fraction(0.40, 2.00) == 0.0


def test_kelly_cap() -> None:
    result = recommend_stake(1000.0, 0.95, 1.50)
    assert result["stake"] <= 50.0
    assert result["pct_bankroll"] <= 0.05


def test_kelly_odds_one() -> None:
    assert kelly_fraction(0.55, 1.0) == 0.0


def test_kelly_odds_below_one() -> None:
    assert kelly_fraction(0.55, 0.5) == 0.0
