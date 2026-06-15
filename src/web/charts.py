"""Chart generators for the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

# Note: These chart functions return dict data structures that can be
# rendered by Streamlit's built-in chart components or passed to
# an optional plotting library.
#
# For Phase 2, we provide data transformation helpers. Interactive
# charts can be enabled by installing altair or plotly.


def prepare_roi_curve(results: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Convert backtest results to cumulative ROI curve data.
    
    Returns: {"bet_number": [...], "cumulative_profit": [...], "balance": [...]}
    """
    balance = 1000.0
    bet_numbers = []
    profits = []
    balances = []
    
    for i, r in enumerate(results, 1):
        bet_numbers.append(i)
        profit = r.get("profit", 0)
        profits.append(profit)
        balance += profit
        balances.append(balance)
    
    # Compute cumulative ROI
    cumulative_profit = []
    running = 0.0
    for p in profits:
        running += p
        cumulative_profit.append(running)
    
    return {
        "bet_number": bet_numbers,
        "cumulative_profit": cumulative_profit,
        "balance": balances,
    }


def prepare_reliability_data(curve: dict[str, Any]) -> dict[str, list[float]]:
    """Convert calibration reliability curve to chart data.
    
    Input: output of calibration.reliability_curve()
    Output: {"bin_center": [...], "mean_predicted": [...], "mean_actual": [...], "count": [...]}
    """
    return {
        "bin_center": curve.get("bin_centers", []),
        "mean_predicted": curve.get("mean_predicted", []),
        "mean_actual": curve.get("mean_actual", []),
        "count": curve.get("counts", []),
    }


def prepare_odds_bucket_data(buckets: dict[str, Any]) -> dict[str, list]:
    """Convert odds bucket analysis to chart data.
    
    Input: output of analysis.odds_bucket_roi()
    Output: {"bucket": [...], "bets": [...], "roi": [...], "win_rate": [...]}
    """
    bucket_names = []
    bet_counts = []
    rois = []
    win_rates = []
    
    for bucket_name, data in sorted(buckets.items()):
        bucket_names.append(bucket_name)
        bet_counts.append(data.get("bets", 0))
        rois.append(data.get("roi", 0.0) * 100)  # Convert to percentage
        win_rates.append(data.get("win_rate", 0.0) * 100)
    
    return {
        "bucket": bucket_names,
        "bets": bet_counts,
        "roi": rois,
        "win_rate": win_rates,
    }


def prepare_drawdown(balances: list[float]) -> dict[str, list[float]]:
    """Compute drawdown series for charting.
    
    Returns: {"balance": [...], "peak": [...], "drawdown_pct": [...]}
    """
    peak = balances[0] if balances else 0
    drawdowns = []
    peaks = []
    
    for b in balances:
        peak = max(peak, b)
        dd = (peak - b) / peak * 100 if peak > 0 else 0
        peaks.append(peak)
        drawdowns.append(dd)
    
    return {
        "balance": balances,
        "peak": peaks,
        "drawdown_pct": drawdowns,
    }
