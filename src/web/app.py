"""Streamlit dashboard for the betting research system."""

from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import date
import io

from src.betting.probabilities import match_outcome_probs
from src.betting.selector import expected_value, is_candidate, select_bets
from src.betting.backtest import run_backtest
from src.betting.calibration import reliability_curve, brier_score, log_loss_score, expected_calibration_error
from src.betting.odds import CsvOddsProvider
from src.betting.features import EloSystem, compute_elo_features, form_features
from src.betting.research import ResearchValidator
from src.schedule import get_upcoming_matches, MATCHES
from src.country_map import get_iso3
from src.predict import predict_all_upcoming
from src.aggregate import normalize_scores
from src.web.charts import (
    build_roi_curve,
    build_reliability_chart,
    build_odds_bucket_chart,
    build_drawdown_chart,
    build_tournament_comparison,
    build_elo_chart,
)

# --- Configuration & Styling ---
st.set_page_config(
    page_title="WC2026 Betting Research",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
:root {
    --bg-color: #0E1117;
    --accent-gold: #FFD700;
    --accent-green: #00C853;
    --accent-red: #FF3D00;
    --card-bg: #1E2127;
    --text-main: #FFFFFF;
    --text-muted: #A0AAB5;
}

body {
    background-color: var(--bg-color);
    color: var(--text-main);
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: var(--bg-color);
}

/* Headers */
h1, h2, h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    color: var(--text-main);
}

/* Cards */
.match-card {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #2B2B2B;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: fadeIn 0.5s ease-out;
}

.match-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    border-color: var(--accent-gold);
}

/* EV Cards */
.ev-card {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
    border-left: 4px solid var(--accent-green);
    animation: fadeIn 0.5s ease-out;
}

.ev-card.high-ev {
    border-left-color: var(--accent-green);
    animation: pulse 2s infinite;
}

.ev-card.med-ev {
    border-left-color: var(--accent-gold);
}

.ev-card.low-ev {
    border-left-color: var(--accent-red);
}

/* KPI Cards */
.kpi-card {
    background-color: var(--card-bg);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #2B2B2B;
}

.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    font-family: monospace;
    color: var(--accent-gold);
}

.kpi-label {
    font-size: 0.9rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0); }
}

/* Data Tables */
.dataframe {
    font-family: monospace;
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# --- Caching & State ---
@st.cache_data
def load_dataset():
    from src.aggregate import build_dataset
    from src.fifa_data import FIFA_DATA
    from src.country_map import COUNTRY_MAP
    from src.cli import _mock_data

    imf_data, bis_rates = _mock_data(COUNTRY_MAP)
    df = build_dataset(imf_data, bis_rates, FIFA_DATA, COUNTRY_MAP)
    return normalize_scores(df)

@st.cache_data
def get_predictions():
    dataset = load_dataset()
    today = date.today().isoformat()
    matches = get_upcoming_matches(today)
    
    # Ensure matches have ISO3 codes
    valid_matches = []
    for m in matches:
        try:
            m_copy = dict(m)
            m_copy["team_a"] = get_iso3(m["team_a"])
            m_copy["team_b"] = get_iso3(m["team_b"])
            valid_matches.append(m_copy)
        except (KeyError, ValueError):
            continue
            
    return predict_all_upcoming(valid_matches, dataset, seed=42)

@st.cache_data
def run_cached_backtest(bankroll, min_ev, min_odds, max_odds, kelly_frac):
    return run_backtest(
        bankroll=bankroll,
        min_ev=min_ev,
        min_odds=min_odds,
        max_odds=max_odds,
        kelly_frac=kelly_frac
    )

# --- Pages ---

def page_today():
    """Page 1: Today's Matches & EV Pipeline."""
    st.title("📊 Today's Matches")
    
    with st.spinner("Loading predictions..."):
        predictions = get_predictions()
        
    if not predictions:
        st.info("No upcoming matches found.")
        return
        
    # Display matches
    st.subheader("Upcoming Fixtures")
    
    # Show top 6 matches in a grid
    cols = st.columns(2)
    for i, pred in enumerate(predictions[:6]):
        col = cols[i % 2]
        with col:
            probs = match_outcome_probs(pred["team_a_clean_xg"], pred["team_b_clean_xg"])
            
            # Determine favorite
            if pred["team_a_blended"] > pred["team_b_blended"] + 0.05:
                fav = pred["team_a"]
            elif pred["team_b_blended"] > pred["team_a_blended"] + 0.05:
                fav = pred["team_b"]
            else:
                fav = "Draw"
                
            html = f"""
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="color: var(--text-muted); font-size: 0.9rem;">{pred.get('date', 'Upcoming')}</span>
                    <span style="background: rgba(255,215,0,0.1); color: var(--accent-gold); padding: 2px 8px; border-radius: 12px; font-size: 0.8rem;">Fav: {fav}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 1.5rem; font-weight: bold;">
                    <span>{pred['team_a']}</span>
                    <span style="color: var(--accent-green);">{pred['predicted_score']}</span>
                    <span>{pred['team_b']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 15px; font-family: monospace; font-size: 0.9rem;">
                    <div style="text-align: center;">
                        <div style="color: var(--text-muted);">1</div>
                        <div>{probs['home']*100:.1f}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: var(--text-muted);">X</div>
                        <div>{probs['draw']*100:.1f}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: var(--text-muted);">2</div>
                        <div>{probs['away']*100:.1f}%</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
            
    st.divider()
    
    # EV Pipeline
    st.subheader("EV Pipeline")
    uploaded_file = st.file_uploader("Upload Odds CSV", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Save uploaded file to a temporary location for CsvOddsProvider
            with open("/tmp/uploaded_odds.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            provider = CsvOddsProvider("/tmp/uploaded_odds.csv")
            odds_data = provider.fetch_odds()
            
            # Get settings
            min_ev = st.session_state.get("min_ev", 0.03)
            min_odds = st.session_state.get("min_odds", 1.50)
            max_odds = st.session_state.get("max_odds", 3.50)
            
            candidates = select_bets(
                predictions, 
                odds_data,
                min_ev=min_ev,
                min_odds=min_odds,
                max_odds=max_odds
            )
            
            if candidates:
                st.success(f"Found {len(candidates)} positive EV candidates!")
                
                for c in candidates:
                    ev_pct = c['ev'] * 100
                    ev_class = "high-ev" if ev_pct > 5 else "med-ev" if ev_pct > 3 else "low-ev"
                    
                    html = f"""
                    <div class="ev-card {ev_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: bold; font-size: 1.2rem;">{c['selection']}</div>
                                <div style="color: var(--text-muted); font-size: 0.9rem;">{c['team_a']} vs {c['team_b']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-family: monospace; font-size: 1.5rem; color: var(--accent-gold);">{c['decimal_odds']:.2f}</div>
                                <div style="color: var(--text-muted); font-size: 0.9rem;">Odds</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-family: monospace; font-size: 1.5rem; color: var(--accent-green);">+{ev_pct:.1f}%</div>
                                <div style="color: var(--text-muted); font-size: 0.9rem;">Edge</div>
                            </div>
                        </div>
                    </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.warning("No positive EV candidates found with current settings.")
                
        except Exception as e:
            st.error(f"Error processing odds: {str(e)}")

def page_backtest():
    """Page 2: Backtest Results."""
    st.title("📈 Backtest Results")
    
    # Settings
    bankroll = st.session_state.get("bankroll", 1000.0)
    min_ev = st.session_state.get("min_ev", 0.03)
    min_odds = st.session_state.get("min_odds", 1.50)
    max_odds = st.session_state.get("max_odds", 3.50)
    kelly_frac = st.session_state.get("kelly_frac", 0.25)
    
    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running historical backtest (2010-2022)..."):
            results = run_cached_backtest(bankroll, min_ev, min_odds, max_odds, kelly_frac)
            st.session_state["backtest_results"] = results
            
    if "backtest_results" in st.session_state:
        results = st.session_state["backtest_results"]
        summary = results["summary"]
        
        # KPI Cards
        cols = st.columns(4)
        kpis = [
            ("Overall ROI", f"{summary['roi']*100:+.2f}%"),
            ("Win Rate", f"{summary['win_rate']*100:.1f}%"),
            ("Total Bets", str(summary['total_bets'])),
            ("Max Drawdown", f"{summary['max_drawdown']*100:.1f}%")
        ]
        
        for i, (label, value) in enumerate(kpis):
            with cols[i]:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-label">{label}</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cumulative Profit Over Time")
            st.line_chart(build_roi_curve(results["results"]), color="#00C853")
            
            st.subheader("ROI by Tournament")
            st.bar_chart(build_tournament_comparison(results["by_tournament"]), color="#FFD700")
            
        with col2:
            st.subheader("Drawdown Profile")
            st.area_chart(build_drawdown_chart([r.get("balance", bankroll) for r in results["results"]]), color="#FF3D00")
            
            st.subheader("Performance by Odds Bucket")
            st.bar_chart(build_odds_bucket_chart(results["by_odds_bucket"]))
            
        # Download Report
        from src.betting.backtest import generate_backtest_report
        report = generate_backtest_report(results)
        st.download_button(
            label="Download Markdown Report",
            data=report,
            file_name="backtest_report.md",
            mime="text/markdown"
        )

def page_calibration():
    """Page 3: Calibration."""
    st.title("📐 Calibration")
    
    if "backtest_results" not in st.session_state:
        st.warning("Please run the backtest first to generate calibration data.")
        return
        
    results = st.session_state["backtest_results"]["results"]
    
    if not results:
        st.info("No bets placed in backtest, cannot compute calibration.")
        return
        
    probs = [r["model_prob"] for r in results]
    outcomes = [1 if r["won"] else 0 for r in results]
    
    # Compute metrics
    brier = brier_score(probs, outcomes)
    logloss = log_loss_score(probs, outcomes)
    ece = expected_calibration_error(probs, outcomes)
    curve = reliability_curve(probs, outcomes)
    
    # KPI Cards
    cols = st.columns(3)
    kpis = [
        ("Brier Score", f"{brier:.4f}"),
        ("Log Loss", f"{logloss:.4f}"),
        ("ECE", f"{ece:.4f}")
    ]
    
    for i, (label, value) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()
    
    # Reliability Chart
    st.subheader("Reliability Diagram")
    df = build_reliability_chart(curve)
    if not df.empty:
        st.scatter_chart(df, x="Predicted", y="Actual", size="Size", color="#FFD700")

def page_research():
    """Page 4: Research."""
    st.title("🔬 Research")
    
    # Initialize Elo
    elo = EloSystem()
    # Dummy data for demonstration
    elo.ratings = {
        "ARG": 1835.4, "FRA": 1832.6, "BRA": 1812.3, "BEL": 1798.1,
        "GBR": 1775.5, "PRT": 1762.8, "NLD": 1758.9, "ESP": 1752.1,
        "HRV": 1745.3, "DEU": 1739.7
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Team Analysis")
        team = st.selectbox("Select Team", sorted(list(elo.ratings.keys())))
        
        if team:
            st.markdown(f"**Elo Rating:** {elo.get_rating(team):.1f}")
            
            # Veto Check
            st.subheader("Veto Simulator")
            opp = st.text_input("Opponent ISO3", "BRA")
            date_str = st.date_input("Match Date").isoformat()
            
            if st.button("Check Veto"):
                validator = ResearchValidator()
                try:
                    validator.load_injuries()
                except FileNotFoundError:
                    pass # Ignore if file doesn't exist for demo
                    
                candidate = {
                    "team_iso3": team,
                    "match_date": date_str,
                    "tournament_stage": "group"
                }
                
                approved, reason = validator.veto_bet(candidate)
                if approved:
                    st.success("✅ Approved: No veto conditions met.")
                else:
                    st.error(f"❌ Vetoed: {reason}")
                    
    with col2:
        st.subheader("Global Elo Rankings")
        st.bar_chart(build_elo_chart(elo.ratings), color="#FFD700")

def page_settings():
    """Page 5: Settings."""
    st.title("⚙️ Settings")
    
    st.markdown("""
    <div class="match-card">
        <h3>Bankroll Management</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state["bankroll"] = st.number_input("Starting Bankroll ($)", value=st.session_state.get("bankroll", 1000.0), step=100.0)
    st.session_state["kelly_frac"] = st.slider("Kelly Fraction", min_value=0.05, max_value=1.0, value=st.session_state.get("kelly_frac", 0.25), step=0.05)
    
    st.markdown("""
    <div class="match-card">
        <h3>Bet Selection Filters</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state["min_ev"] = st.slider("Minimum EV Threshold", min_value=0.0, max_value=0.20, value=st.session_state.get("min_ev", 0.03), step=0.01, format="%.2f")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["min_odds"] = st.number_input("Minimum Odds", value=st.session_state.get("min_odds", 1.50), step=0.1)
    with col2:
        st.session_state["max_odds"] = st.number_input("Maximum Odds", value=st.session_state.get("max_odds", 3.50), step=0.1)
        
    st.markdown("""
    <div class="match-card">
        <h3>Model Parameters</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state["rho"] = st.slider("Dixon-Coles Rho (Low-score correlation)", min_value=-0.2, max_value=0.2, value=st.session_state.get("rho", 0.0), step=0.01)
    st.session_state["market"] = st.selectbox("Default Market", ["1X2", "DNB", "AH-0.5", "BTTS"])

# --- Navigation ---
PAGES = {
    "📊 Today's Matches": page_today,
    "📈 Backtest": page_backtest,
    "📐 Calibration": page_calibration,
    "🔬 Research": page_research,
    "⚙️ Settings": page_settings,
}

st.sidebar.title("WC2026 Betting")
st.sidebar.markdown("---")
selection = st.sidebar.radio("Navigation", list(PAGES.keys()))

# Render selected page
PAGES[selection]()
