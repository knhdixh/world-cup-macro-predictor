"""Closing Line Value (CLV) tracker for evaluating bet selection."""

from __future__ import annotations

from statistics import median
from typing import Any

__all__ = ["compute_clv", "clv_summary", "clv_by_odds_bucket"]


def compute_clv(odds_taken: float, closing_odds: float) -> float:
    """Compute Closing Line Value.

    Positive CLV = the odds you took were better than the closing market.
    CLV = (odds_taken - closing_odds) / odds_taken

    If closing_odds is unavailable (None), returns 0.0.
    """
    if closing_odds is None:
        return 0.0
    if odds_taken == 0:
        return 0.0
    return (odds_taken - closing_odds) / odds_taken


def clv_summary(bets: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate CLV metrics across a set of bets."""
    clvs: list[float] = []
    positive = 0
    bets_with_closing = 0

    for bet in bets:
        odds_taken = bet.get("odds_taken")
        closing_odds = bet.get("closing_odds")
        if odds_taken is None:
            continue
        clv = compute_clv(float(odds_taken), closing_odds)
        clvs.append(clv)
        if closing_odds is not None:
            bets_with_closing += 1
        if clv > 0:
            positive += 1

    total_bets = len(bets)
    mean_clv = sum(clvs) / len(clvs) if clvs else 0.0
    median_clv = median(clvs) if clvs else 0.0
    positive_clv_pct = (positive / total_bets * 100.0) if total_bets else 0.0

    return {
        "mean_clv": float(mean_clv),
        "median_clv": float(median_clv),
        "positive_clv_pct": float(positive_clv_pct),
        "total_bets": total_bets,
        "bets_with_closing": bets_with_closing,
    }


def clv_by_odds_bucket(bets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """CLV broken down by odds ranges."""
    buckets = {
        "1.01-1.50": [],
        "1.50-2.00": [],
        "2.00-3.00": [],
        "3.00-5.00": [],
        "5.00+": [],
    }

    for bet in bets:
        odds_taken = bet.get("odds_taken")
        if odds_taken is None:
            continue
        odds_taken_f = float(odds_taken)
        clv = compute_clv(odds_taken_f, bet.get("closing_odds"))

        if 1.01 <= odds_taken_f < 1.50:
            buckets["1.01-1.50"].append(clv)
        elif 1.50 <= odds_taken_f < 2.00:
            buckets["1.50-2.00"].append(clv)
        elif 2.00 <= odds_taken_f < 3.00:
            buckets["2.00-3.00"].append(clv)
        elif 3.00 <= odds_taken_f < 5.00:
            buckets["3.00-5.00"].append(clv)
        elif odds_taken_f >= 5.00:
            buckets["5.00+"].append(clv)

    result: dict[str, dict[str, float]] = {}
    for label, values in buckets.items():
        count = len(values)
        result[label] = {
            "count": count,
            "mean_clv": float(sum(values) / count) if count else 0.0,
            "positive_pct": float((sum(1 for value in values if value > 0) / count) * 100.0)
            if count
            else 0.0,
        }
    return result
