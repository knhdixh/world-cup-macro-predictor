# Phase 2 Learnings

## Historical Match Database

- Created `HistoricalDB` class in `src/betting/historical.py`
- Data files live under `data/historical/` — 4 fixture CSVs + 4 ranking CSVs
- Uses actual World Cup group-stage results (48 matches × 4 tournaments = 192 total)
- Simulated odds computed via Elo prediction formula with flat 25% draw baseline
  - `P(home) = elo_p * 0.75` where `elo_p = 1/(1+10^((rating_b-rating_a)/400))`
  - `P(draw) = 0.25`
  - `P(away) = (1-elo_p) * 0.75`
  - Decimal odds = 1/(P * 0.95) for ~5% overround
- Important: flat 25% draw needed scaling (multiply Elo split by 0.75) to avoid negative away probability for extreme mismatches
- ISO3 codes consistent with Phase 1 (GBR for England, etc.)
- New historical ISO3 codes added: NGA, GRC, SVN, SRB, DNK, CMR, ITA, SVK, PRK, HND, CHL, RUS, PER, ISL, CRI, POL, WAL

## Backtesting Engine

- Created `src/betting/backtest.py` — `run_backtest()`, `_simulate_match_outcome()`, `generate_backtest_report()`, `_max_drawdown()`
- Created `tests/betting/test_backtest.py` — 3 tests (structure, ARG vs SAU outcome, max drawdown)
- `run_backtest()` replays Phase 1 betting model on 192 historical WC matches (2010-2022)
- **xG from FIFA proxy**: Since no historical economic data, FIFA points are min-max normalized per tournament (0-1), then mapped as xG = normalized * 4. This is the proxy for the blended score.
- `_simulate_match_outcome()` handles a single match: Poisson probs → EV check → Kelly staking → profit/loss from actual result
- Default filters: min_ev=0.03, min_odds=1.50, max_odds=3.50, kelly_frac=0.25
- QA results: 147 bets across 4 tournaments, 7.19% ROI, 57.14% win rate, 29.68% max drawdown (with min_ev=0.05)
- Notable: 2014 was the best tournament (21.31% ROI), 2010 had only 2 bets (very few positive-EV opportunities with the FIFA-only proxy)
- Returns comprehensive dict with results, summary, by_tournament, by_odds_bucket, by_market analysis
- All 157 tests pass (154 existing + 3 new)
