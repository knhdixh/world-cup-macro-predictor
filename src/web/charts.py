"""Chart generators for the Streamlit dashboard using Streamlit native charts."""

from __future__ import annotations

from typing import Any
import pandas as pd

def build_roi_curve(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a cumulative ROI line chart data."""
    if not results:
        return pd.DataFrame()
        
    profits = [r.get("profit", 0) for r in results]
    cumulative_profit = []
    running = 0.0
    for p in profits:
        running += p
        cumulative_profit.append(running)
        
    bet_numbers = list(range(1, len(results) + 1))
    
    df = pd.DataFrame({
        "Bet Number": bet_numbers,
        "Cumulative Profit": cumulative_profit
    })
    return df.set_index("Bet Number")

def build_reliability_chart(curve: dict[str, Any]) -> pd.DataFrame:
    """Build a reliability diagram data."""
    if not curve or not curve.get("bin_centers"):
        return pd.DataFrame()
        
    bin_centers = curve["bin_centers"]
    mean_predicted = curve["mean_predicted"]
    mean_actual = curve["mean_actual"]
    counts = curve["counts"]
    
    # Filter out empty bins
    valid_idx = [i for i, c in enumerate(counts) if c > 0]
    x_vals = [mean_predicted[i] for i in valid_idx]
    y_vals = [mean_actual[i] for i in valid_idx]
    sizes = [counts[i] * 10 for i in valid_idx] # Scale for visibility
    
    df = pd.DataFrame({
        "Predicted": x_vals,
        "Actual": y_vals,
        "Count": [counts[i] for i in valid_idx],
        "Size": sizes
    })
    return df

def build_odds_bucket_chart(buckets: dict[str, Any]) -> pd.DataFrame:
    """Build a grouped bar chart data for odds buckets."""
    if not buckets:
        return pd.DataFrame()
        
    bucket_names = []
    rois = []
    win_rates = []
    
    for name, data in sorted(buckets.items()):
        bucket_names.append(name)
        rois.append(data.get("roi", 0.0) * 100)
        win_rates.append(data.get("win_rate", 0.0) * 100)
        
    df = pd.DataFrame({
        "Odds Range": bucket_names,
        "ROI (%)": rois,
        "Win Rate (%)": win_rates
    })
    return df.set_index("Odds Range")

def build_drawdown_chart(balances: list[float]) -> pd.DataFrame:
    """Build an area chart data showing drawdown."""
    if not balances:
        return pd.DataFrame()
        
    peak = balances[0] if balances else 0
    drawdowns = []
    
    for b in balances:
        peak = max(peak, b)
        dd = (peak - b) / peak * 100 if peak > 0 else 0
        drawdowns.append(-dd) # Negative for visual effect
        
    df = pd.DataFrame({
        "Bet Number": list(range(len(drawdowns))),
        "Drawdown (%)": drawdowns
    })
    return df.set_index("Bet Number")

def build_tournament_comparison(results: dict[str, Any]) -> pd.DataFrame:
    """Build a bar chart data comparing tournament ROIs."""
    if not results:
        return pd.DataFrame()
        
    tournaments = []
    rois = []
    
    for year, data in sorted(results.items()):
        tournaments.append(str(year))
        roi = data.get("roi", 0.0) * 100
        rois.append(roi)
        
    df = pd.DataFrame({
        "Tournament": tournaments,
        "ROI (%)": rois
    })
    return df.set_index("Tournament")

def build_elo_chart(ratings: dict[str, float]) -> pd.DataFrame:
    """Build a horizontal bar chart data of top 10 Elo ratings."""
    if not ratings:
        return pd.DataFrame()
        
    # Sort and get top 10
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:10]
    
    teams = [x[0] for x in sorted_ratings]
    scores = [x[1] for x in sorted_ratings]
    
    df = pd.DataFrame({
        "Team": teams,
        "Elo Rating": scores
    })
    return df.set_index("Team")
