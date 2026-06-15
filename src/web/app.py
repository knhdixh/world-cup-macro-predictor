"""Streamlit dashboard for the betting research system."""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import date

from src.betting.probabilities import match_outcome_probs
from src.betting.selector import expected_value, is_candidate
from src.schedule import get_upcoming_matches, MATCHES
from src.country_map import get_iso3


st.set_page_config(
    page_title="World Cup Betting Research",
    page_icon="⚽",
    layout="wide",
)


def page_today():
    """Page 1: Today's matches with model predictions and EV."""
    st.header("Today's Matches")
    today = date.today().isoformat()
    matches = get_upcoming_matches(today)[:10]  # Show next 10
    
    data = []
    for m in matches:
        try:
            team_a = get_iso3(m["team_a"])
            team_b = get_iso3(m["team_b"])
        except (KeyError, ValueError):
            continue
        
        data.append({
            "Date": m["date"],
            "Group": m.get("group", ""),
            "Home": m["team_a"],
            "Away": m["team_b"],
        })
    
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No upcoming matches found.")


def page_candidates():
    """Page 2: Ranked EV candidates."""
    st.header("EV Candidates")
    st.info("Load an odds CSV via the CLI to see EV candidates here.")
    st.code("python -m src.betting.cli --odds odds.csv --no-fetch --bankroll 1000")


def page_backtest():
    """Page 3: Backtest performance."""
    st.header("Backtest Results")
    st.info("Run the backtest CLI command to populate results:")
    st.code("python -m src.betting.cli backtest --bankroll 1000")


def page_calibration():
    """Page 4: Calibration report."""
    st.header("Calibration Report")
    st.info("Calibration data will appear here after running the calibration pipeline.")


# Navigation
PAGES = {
    "Today's Matches": page_today,
    "EV Candidates": page_candidates,
    "Backtest": page_backtest,
    "Calibration": page_calibration,
}

st.sidebar.title("WC2026 Betting Research")
selection = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[selection]()
