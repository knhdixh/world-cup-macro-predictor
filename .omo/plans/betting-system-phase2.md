# Football Betting Research System — Phase 2

## TL;DR

> **Quick Summary**: Upgrade the Phase 1 MVP paper-betting pipeline with historical backtesting, probability calibration, market expansion, research validation, and web dashboard — transforming it from a live-only paper system into a validated, production-ready betting research platform.
>
> **Deliverables**:
> - Historical match database + backtesting engine (WC 2010-2022)
> - Probability calibration (Brier score, reliability curves, log loss)
> - Closing Line Value (CLV) tracking + odds bucket analysis
> - Research validator (injuries, lineups, weather, rest days, motivation)
> - Dixon-Coles low-score correlation adjustment
> - DNB & Asian handicap markets
> - Elo/SPI/squad-value feature engineering
> - Web dashboard (Streamlit)
> - Live odds API integration
>
> **Estimated Effort**: Large (18 implementation tasks + 4 final verification)
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 14 → Task 18 → F1-F4

---

## Context

### What Phase 1 Delivered
- Clean xG extraction from macro-FIFA predictor
- Pure Python Poisson probability engine (1X2, Totals, BTTS)
- Odds CSV parser + overround normalization
- EV calculator + quarter-Kelly staking engine
- Paper bet ledger (17-column CSV)
- CLI: `python -m src.betting.cli --odds odds.csv --bankroll 1000`
- 143/143 tests passing

### What Phase 2 Adds
Phase 1 catches live EV signals but has no way to validate them historically. Phase 2 adds:
1. **Backtesting** — run the model on 250+ past World Cup matches to measure real performance
2. **Calibration** — fix the model's probability overconfidence (xG multiplier 4.0 never validated)
3. **CLV** — track whether model odds beat the closing market line
4. **Research** — prevent obvious bad bets (injured star player, etc.)
5. **Market expansion** — DNB, Asian handicap, corrected BTTS (Dixon-Coles)
6. **Dashboard** — visual interface to browse predictions and track performance

---

## Work Objectives

### Core Objective
Upgrade the Phase 1 paper-betting pipeline into a validated research system with historical backtesting, probability calibration, market expansion (DNB, Asian handicap), research validation, and a web dashboard.

### Concrete Deliverables
**Backtesting & Calibration:**
- `src/betting/backtest.py` — historical match database + backtesting engine
- `src/betting/calibration.py` — Brier score, log loss, reliability curves
- `src/betting/clv.py` — Closing Line Value tracker
- `data/historical/` — WC 2010/2014/2018/2022 match + odds data

**Market Expansion:**
- `src/betting/markets.py` — DNB, Asian handicap, Dixon-Coles BTTS
- Updates to `probabilities.py` — Dixon-Coles ρ parameter

**Features:**
- `src/betting/features.py` — Elo rating, squad value, form tracker
- `src/betting/research.py` — injury/lineup/weather/motivation validator

**Dashboard:**
- `src/web/` — Streamlit dashboard (predictions, EV rankings, performance charts)

**Odds:**
- `src/betting/api_odds.py` — The Odds API provider (live odds)

### Must Have
- Backtesting on WC 2010-2022 with per-tournament ROI
- Calibration report: Brier score, reliability curve, log loss
- CLV tracking: model odds vs closing odds
- DNB + Asian handicap -0.5 markets
- Dixon-Coles adjustment for BTTS
- Streamlit dashboard: today's matches, EV rankings, performance history
- Research validator: injury checks with veto power

### Must NOT Have (Guardrails)
- NO real-money betting — paper only
- NO automated Bet365 scraping — use The Odds API or manual CSV
- NO model modification of `formula.py`, `aggregate.py`, `fifa_data.py`
- NO breaking changes to Phase 1 CLI
- NO database dependency — CSV/Parquet for historical data

---

## Verification Strategy

- **Test Strategy**: TDD (RED → GREEN → REFACTOR), existing pytest infrastructure
- **QA Policy**: Agent-executed QA scenarios for every task
- **Evidence**: `.omo/evidence/task-{N}-*.txt`

---

## Execution Strategy

```
Wave 1 (Start Immediately — data + calibration: 5 tasks, ALL parallel):
├── Task 1: Historical match database (WC 2010-2022) [unspecified-high]
├── Task 2: Backtesting engine [unspecified-high]
├── Task 3: Probability calibration (Brier, log loss, reliability) [quick]
├── Task 4: CLV tracker [quick]
└── Task 5: Odds bucket analysis (1.50-2.00, 2.00-3.00, etc.) [quick]

Wave 2 (After Wave 1 — markets + features: 5 tasks, ALL parallel):
├── Task 6: Dixon-Coles adjustment for BTTS [quick]
├── Task 7: DNB market calculator [quick]
├── Task 8: Asian handicap -0.5 market [quick]
├── Task 9: Elo rating + squad value features [unspecified-high]
└── Task 10: Research validator (injuries, lineups, weather) [unspecified-high]

Wave 3 (After Wave 2 — odds API: 2 tasks):
├── Task 11: The Odds API provider [unspecified-high]
└── Task 12: Odds provider registry (CSV + API) [quick]

Wave 4 (After Wave 3 — dashboard + integration: 4 tasks):
├── Task 13: Streamlit dashboard core [visual-engineering]
├── Task 14: Performance charts + calibration viz [visual-engineering]
├── Task 15: CLI extension (--backtest, --calibrate flags) [quick]
└── Task 16: Integration test suite [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan compliance audit [oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real manual QA [unspecified-high]
└── Task F4: Scope fidelity check [deep]
```

---

## TODOs

- [x] 1. Historical match database — WC 2010/2014/2018/2022 data

  **What to do**:
  - Create `src/betting/historical.py` with a `HistoricalDB` class
  - Build a dataset of all World Cup group-stage matches from 2010, 2014, 2018, 2022
  - For each match: date, teams, FIFA rankings at time of match, match result (home goals, away goals)
  - Store as CSV in `data/historical/` directory
  - Include pre-match odds (closing odds from Bet365/Pinnacle if available, otherwise use simulated odds based on FIFA ranking differential)
  - Minimum: ~256 matches (64 per tournament × 4 tournaments)
  - Create `tests/betting/test_historical.py` with 3 tests
  - Run existing test suite to confirm zero regressions

  **Recommended Agent Profile**: `unspecified-high` — significant data collection + schema design
  **Can Run In Parallel**: YES (Wave 1, with Tasks 2-5)
  **Blocks**: Task 2 (backtesting engine needs data)
  **Blocked By**: None

- [x] 2. Backtesting engine — replay Phase 1 model on historical data

  **What to do**:
  - Create `src/betting/backtest.py`
  - `run_backtest(matches, odds, bankroll=1000) -> dict`: For each historical match, run the Phase 1 prediction pipeline (clean xG → 1X2 probs → EV → Kelly → simulated bet), track results
  - Output: ROI, yield, profit curve, max drawdown, win rate, profit factor
  - Support: per-tournament breakdown, per-odds-bucket breakdown
  - `generate_backtest_report(results) -> str`: Markdown-formatted report
  - Tests: `tests/betting/test_backtest.py` with 3 tests (known match outcomes, bankroll tracking, profit calculation)

  **Recommended Agent Profile**: `unspecified-high` — complex logic with financial tracking
  **Can Run In Parallel**: NO (needs Task 1 data)
  **Blocks**: Task 14 (dashboard charts)
  **Blocked By**: Task 1

- [x] 3. Probability calibration — Brier score, log loss, reliability curves

  **What to do**:
  - Create `src/betting/calibration.py`
  - `brier_score(probs: list[float], outcomes: list[int]) -> float`: Mean squared error between predicted probability and actual outcome
  - `log_loss_score(probs, outcomes) -> float`: Logarithmic loss
  - `reliability_curve(probs, outcomes, bins=10) -> dict`: Group predictions into probability buckets (0-10%, 10-20%, etc.), compare predicted vs actual frequency in each bucket
  - `expected_calibration_error(probs, outcomes, bins=10) -> float`: ECE metric
  - Tests: `tests/betting/test_calibration.py` with 3 tests

  **Recommended Agent Profile**: `quick` — pure math functions
  **Can Run In Parallel**: YES (Wave 1, with Tasks 1, 2, 4, 5)
  **Blocks**: Task 14 (dashboard calibration viz)
  **Blocked By**: None (pure math, no deps)

- [x] 4. CLV tracker — Closing Line Value analysis

  **What to do**:
  - Create `src/betting/clv.py`
  - `compute_clv(odds_taken: float, closing_odds: float) -> float`: Positive if beating the market
  - `clv_summary(bets: list[dict]) -> dict`: Mean CLV, median CLV, % of bets with positive CLV
  - `clv_by_odds_bucket(bets: list[dict]) -> dict`: CLV broken down by odds ranges
  - Tests: `tests/betting/test_clv.py` with 3 tests

  **Recommended Agent Profile**: `quick` — simple math + aggregation
  **Can Run In Parallel**: YES (Wave 1)
  **Blocks**: Task 14 (dashboard)
  **Blocked By**: None

- [x] 5. Odds bucket analysis — ROI by odds range

  **What to do**:
  - Add to `src/betting/backtest.py` or create `src/betting/analysis.py`
  - `odds_bucket_roi(results: list[dict]) -> dict`: Group bets by odds ranges (1.20-1.50, 1.50-2.00, 2.00-3.00, 3.00+) and compute ROI per bucket
  - `market_roi_matrix(results: list[dict]) -> dict`: ROI by market type (1X2 vs totals vs BTTS)
  - Tests: `tests/betting/test_analysis.py` with 2 tests

  **Recommended Agent Profile**: `quick`
  **Can Run In Parallel**: YES (Wave 1)
  **Blocks**: Task 14
  **Blocked By**: None

- [x] 6. Dixon-Coles adjustment — low-score correlation for BTTS

  **What to do**:
  - Modify `src/betting/probabilities.py`: add `dixon_coles_rho` parameter to `match_outcome_probs()` and `btts_probs()`
  - Dixon-Coles adjusts the joint probability for low-scoring outcomes (0-0, 1-0, 0-1, 1-1) using a correlation parameter ρ
  - P(i,j) = τ × Poisson(i|λ_h) × Poisson(j|λ_a) × DC_factor(i,j,ρ)
  - where DC_factor = 1 − λ_h × λ_a × ρ if (i,j) ∈ {(0,0),(1,0),(0,1),(1,1)}
  - τ is a normalization constant to ensure sum=1.0
  - Default ρ = 0 (no adjustment); set ρ = -0.05 as reasonable starting point
  - Update existing tests to still pass (at ρ=0, behavior unchanged); add test with ρ=-0.05
  - Tests: 2 new test functions in test_probabilities.py

  **Recommended Agent Profile**: `quick` — formula modification
  **Can Run In Parallel**: YES (Wave 2)
  **Blocks**: None (enhancement, not breaking)
  **Blocked By**: None (depends only on existing probabilities.py)

- [x] 7. DNB market calculator — Draw No Bet

  **What to do**:
  - Create `src/betting/markets.py`
  - `dnb_probs(xg_home, xg_away, max_goals=10) -> dict`: P(home wins | no draw) = p_home / (p_home + p_away), P(away wins | no draw) = p_away / (p_home + p_away)
  - `asian_handicap_probs(xg_home, xg_away, line=-0.5, max_goals=10) -> dict`: For -0.5 handicap (favorite gives 0.5 goal): adjust home xG up by 0.5, compute new probs. For +0.5: adjust away xG.
  - Tests: `tests/betting/test_markets.py` with 4 tests

  **Recommended Agent Profile**: `quick` — simple probability derivations
  **Can Run In Parallel**: YES (Wave 2)
  **Blocks**: Task 15 (CLI flags for new markets)
  **Blocked By**: None (depends on probabilities.py from Phase 1)

- [x] 8. Elo rating + squad value features

  **What to do**:
  - Create `src/betting/features.py`
  - `EloSystem` class: maintain Elo ratings for all 48 nations, update after each match
  - Start Elo at 1500 with K=32 for World Cup matches
  - `compute_elo_features(team_a, team_b) -> dict`: elo_diff, elo_win_prob
  - `squad_value_features(team_a, team_b) -> dict`: placeholder for squad market value (read from a CSV if available, otherwise use FIFA ranking as proxy)
  - `form_features(team_a, team_b) -> dict`: recent form (last 5 matches: W/D/L record)
  - Tests: `tests/betting/test_features.py` with 4 tests

  **Recommended Agent Profile**: `unspecified-high` — algorithmic rating system
  **Can Run In Parallel**: YES (Wave 2)
  **Blocks**: None
  **Blocked By**: None

- [x] 9. Research validator — injury/lineup/weather checks

  **What to do**:
  - Create `src/betting/research.py`
  - `ResearchValidator` class with methods:
    - `check_injuries(team: str) -> list[str]`: Check for known injuries (read from a CSV or simple config file)
    - `check_rest_days(match_date: str, team_last_match: str) -> int`: Days since last match
    - `check_motivation(match: dict) -> str`: Tournament stage motivation ("must-win", "dead rubber", "normal")
    - `veto_bet(candidate: dict) -> tuple[bool, str]`: Return (approved, reason). Reject if key player injured, < 3 rest days, or dead rubber match
  - Configuration: `data/research/injuries.csv` with known injuries
  - Tests: `tests/betting/test_research.py` with 3 tests

  **Recommended Agent Profile**: `unspecified-high` — complex decision logic
  **Can Run In Parallel**: YES (Wave 2)
  **Blocks**: Task 15 (CLI integration)
  **Blocked By**: None

- [ ] 10. The Odds API provider — live odds integration

  **What to do**:
  - Create `src/betting/api_odds.py`
  - `ApiOddsProvider` class implementing the `OddsProvider` protocol from Phase 1
  - Fetches odds from The Odds API (free tier: https://the-odds-api.com/)
  - Requires API key stored in environment variable `ODDS_API_KEY`
  - `fetch_odds(sport="soccer_world_cup", regions="uk", markets="h2h") -> list[dict]`: Fetches and transforms to Phase 1 CSV schema format
  - Handle rate limiting, API errors, and missing events gracefully
  - Tests: mock the API responses with `pytest-mock`

  **Recommended Agent Profile**: `unspecified-high` — API integration with error handling
  **Can Run In Parallel**: YES (Wave 3, with Task 11)
  **Blocks**: Task 15
  **Blocked By**: None

- [ ] 11. Odds provider registry — unified odds interface

  **What to do**:
  - Create `src/betting/providers.py`
  - `OddsProviderRegistry` class: register multiple providers, fetch from all, merge results
  - `get_odds(method="csv", **kwargs) -> list[dict]`: Unified interface. If method="csv", return CsvOddsProvider results. If method="api", return ApiOddsProvider results. If method="auto", try API first, fall back to CSV.
  - Update CLI to support `--odds-method auto|api|csv`
  - Tests: `tests/betting/test_providers.py` with 2 tests

  **Recommended Agent Profile**: `quick` — registry pattern
  **Can Run In Parallel**: NO (needs Task 10)
  **Blocks**: Task 15
  **Blocked By**: Task 10

- [ ] 12. Streamlit dashboard — core layout

  **What to do**:
  - Create `src/web/app.py` — Streamlit app entry point
  - Pages:
    1. **Today** — upcoming matches with model predictions, odds, and EV values
    2. **Candidates** — ranked EV candidates with Kelly stakes (from CLI output)
    3. **Backtest** — historical performance charts (ROI over time, drawdown)
    4. **Calibration** — reliability curve, Brier score over time
  - Use Streamlit caching for model predictions
  - `pip install streamlit` added to pyproject.toml optional-dependencies
  - Launch: `streamlit run src/web/app.py`
  - Tests: `tests/web/test_app.py` with 2 smoke tests (app starts, pages render)

  **Recommended Agent Profile**: `visual-engineering` — UI/UX design
  **Can Run In Parallel**: YES (Wave 4, with Tasks 13-15)
  **Blocks**: None
  **Blocked By**: Tasks 2, 3, 4 (needs backtest + calibration data for charts)

- [ ] 13. Performance charts — calibration + ROI visualization

  **What to do**:
  - Create `src/web/charts.py`
  - `plot_roi_curve(results: list[dict]) -> altair.Chart`: Cumulative ROI over time
  - `plot_reliability_curve(calibration: dict) -> altair.Chart`: Reliability diagram
  - `plot_odds_bucket_roi(analysis: dict) -> altair.Chart`: Bar chart of ROI by odds bucket
  - `plot_drawdown(results: list[dict]) -> altair.Chart`: Drawdown curve
  - Use Altair or Plotly for interactive charts
  - Tests: 1 smoke test per chart

  **Recommended Agent Profile**: `visual-engineering` — data visualization
  **Can Run In Parallel**: YES (Wave 4)
  **Blocks**: None
  **Blocked By**: Tasks 2-5

- [ ] 14. CLI extension — Phase 2 flags

  **What to do**:
  - Extend `src/betting/cli.py` with new subcommands:
    - `python -m src.betting.cli backtest` — run backtest on historical data
    - `python -m src.betting.cli calibrate` — generate calibration report
    - `python -m src.betting.cli research VETO` — research validator check
  - Add `--market` flag to existing pipeline: support "1X2", "DNB", "AH-0.5", "BTTS", "O2.5"
  - Integrate research validator into existing pipeline (bet candidates are vetoed if research flags issues)
  - Add `--odds-method auto|csv|api` flag
  - Tests: 3 new CLI integration tests

  **Recommended Agent Profile**: `quick` — CLI extension
  **Can Run In Parallel**: NO (depends on multiple tasks)
  **Blocks**: Task 16 (integration)
  **Blocked By**: Tasks 7-11

- [ ] 15. Integration test suite — end-to-end Phase 2

  **What to do**:
  - Create `tests/betting/test_phase2_integration.py`
  - Test: full backtest pipeline runs end-to-end with mock historical data
  - Test: calibration report generates all metrics
  - Test: CLI backtest subcommand works
  - Test: Streamlit app imports without error
  - Regression: all 143 Phase 1 tests still pass
  - `python -m pytest tests/ -v` → all pass

  **Recommended Agent Profile**: `quick`
  **Can Run In Parallel**: NO (needs all tasks complete)
  **Blocks**: None (last task before Final Wave)
  **Blocked By**: All previous tasks

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify: all Must Have present, all Must NOT Have absent, regression gate passes.

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run full test suite, check for slop, verify no forbidden imports.

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Execute backtest pipeline, run calibration, launch dashboard, check CLI.

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify all planned files exist, no unplanned modifications.

---

## Commit Strategy

- **1-5** (Wave 1): `feat(phase2): add historical database, backtesting, and calibration`
- **6-9** (Wave 2): `feat(phase2): add Dixon-Coles, DNB, Asian handicap, Elo features, research validator`
- **10-11** (Wave 3): `feat(phase2): add odds API provider and unified registry`
- **12-15** (Wave 4): `feat(phase2): add Streamlit dashboard, CLI extensions, and integration tests`

---

## Success Criteria

### Verification Commands
```bash
# Backtest pipeline
python -m src.betting.cli backtest --data data/historical/ --bankroll 1000

# Calibration report
python -m src.betting.cli calibrate --data data/historical/

# All markets
python -m src.betting.cli --odds odds.csv --market DNB --no-fetch

# Dashboard
streamlit run src/web/app.py

# Full test suite (Phase 1 + Phase 2)
python -m pytest tests/ -v
```
