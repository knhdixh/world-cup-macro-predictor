"""Post-backtest analysis: ROI by odds buckets and markets."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any


def odds_bucket_roi(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Compute ROI grouped by decimal odds ranges.

    Standard buckets: 1.01-1.50, 1.50-2.00, 2.00-3.00, 3.00-5.00, 5.00+

    Each result dict should have: "decimal_odds", "profit", "stake"

    Returns dict mapping bucket label -> {
        "bets": count,
        "total_stake": sum of stakes,
        "total_profit": sum of profits,
        "roi": profit/stake as fraction,
        "win_rate": wins/total,
    }

    Returns empty dict if results is empty.
    """
    if not results:
        return {}

    buckets: dict[str, dict[str, float]] = OrderedDict()
    for row in results:
        bucket = _get_bucket(float(row["decimal_odds"]))
        summary = buckets.setdefault(
            bucket,
            {
                "bets": 0.0,
                "total_stake": 0.0,
                "total_profit": 0.0,
                "roi": 0.0,
                "win_rate": 0.0,
            },
        )
        stake = float(row["stake"])
        profit = float(row["profit"])
        summary["bets"] += 1.0
        summary["total_stake"] += stake
        summary["total_profit"] += profit
        if profit > 0:
            summary.setdefault("wins", 0.0)
            summary["wins"] += 1.0

    for summary in buckets.values():
        total_stake = summary["total_stake"]
        total_profit = summary["total_profit"]
        bets = summary["bets"]
        wins = summary.pop("wins", 0.0)
        summary["roi"] = total_profit / total_stake if total_stake else 0.0
        summary["win_rate"] = wins / bets if bets else 0.0

    return dict(buckets)


def market_roi_matrix(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Compute ROI grouped by market type (1X2, totals, BTTS, etc.).

    Each result dict should have: "market", "profit", "stake"

    Returns dict mapping market -> {
        "bets": count,
        "total_stake": sum of stakes,
        "total_profit": sum of profits,
        "roi": profit/stake as fraction,
    }
    """
    matrix: dict[str, dict[str, float]] = OrderedDict()
    for row in results:
        market = str(row["market"])
        summary = matrix.setdefault(
            market,
            {
                "bets": 0.0,
                "total_stake": 0.0,
                "total_profit": 0.0,
                "roi": 0.0,
            },
        )
        summary["bets"] += 1.0
        summary["total_stake"] += float(row["stake"])
        summary["total_profit"] += float(row["profit"])

    for summary in matrix.values():
        total_stake = summary["total_stake"]
        summary["roi"] = summary["total_profit"] / total_stake if total_stake else 0.0

    return dict(matrix)


def _get_bucket(odds: float) -> str:
    """Return the bucket label for a given decimal odds value."""
    if odds < 1.50:
        return "1.01-1.50"
    elif odds < 2.00:
        return "1.50-2.00"
    elif odds < 3.00:
        return "2.00-3.00"
    elif odds < 5.00:
        return "3.00-5.00"
    else:
        return "5.00+"
