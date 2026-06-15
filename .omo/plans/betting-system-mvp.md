# Football Betting Research System — MVP Phase 1

## TL;DR

> **Quick Summary**: Transform the existing World Cup 2026 macro-football predictor into a paper-betting research system that converts model xG into calibrated match-outcome probabilities, compares against Bet365 odds (manual CSV input), and outputs positive-EV bet candidates with fractional-Kelly stake sizing.
>
> **Deliverables**:
> - Clean xG extraction from existing predictor (noise-free probabilities)
> - Poisson probability engine: 1X2, Totals (O/U 2.5), BTTS markets
> - Odds CSV parser with provider interface + overround normalization
> - EV calculator + quarter-Kelly staking with 5% bankroll cap
> - Paper bet ledger (CSV append-only)
> - CLI: `python -m src.betting.cli --odds odds.csv --bankroll 1000`
>
> **Estimated Effort**: Medium (12 implementation tasks + 4 final verification)
> **Parallel Execution**: YES — 4 waves (1 → 2a → 2b → 3)
> **Critical Path**: Task 1 → Task 2 → Task 3 → Task 8 → Task 9 → Task 10 → Task 11 → F1-F4

---

## Context

### Original Request
User wants to build a football betting research system on top of the existing World Cup 2026 macro-football predictor, inspired by two reference repos: `knhdixh/world-cup-macro-predictor` (the current codebase's origin) and `kyleskom/NBA-Machine-Learning-Sports-Betting` (architecture patterns to borrow). The system should use Bet365 odds (manual CSV input — NO scraping), compute expected value, and recommend bets with proper stake sizing.

### Interview Summary
**Key Discussions**:
- **Phased MVP**: Phase 1 builds the minimum for paper betting (probability engine + odds parser + EV/Kelly + ledger). Phase 2 adds backtesting, calibration, research validator, dashboard, CLV tracking.
- **TDD**: All betting modules developed RED → GREEN → REFACTOR, leveraging existing pytest infrastructure.
- **Markets**: 1X2 (primary), Totals O/U 2.5 and BTTS (secondary, trivial derivations from same Poisson grid). DNB and Asian handicap deferred to Phase 2.
- **Odds**: Manual CSV input with provider interface architecture (API plugins in Phase 2).
- **Staking**: Quarter-Kelly (fraction=0.25), 5% bankroll hard cap per bet.
- **CLI-only**: No web dashboard in Phase 1.
- **Historical**: Schema designed for WC 2010-2022 data; actual backtesting in Phase 2.
- **Group stage only**: Knockout matches contain placeholders and are skipped.

**Research Findings**:
- Existing `predict_match()` returns noisy xG only — must add clean xG to return dict (Option C: backward-compatible key addition).
- `scipy` is NOT in `pyproject.toml` — pure Python Poisson PMF avoids a heavy dependency.
- The `xG = blended * 4` multiplier has never been calibrated against real WC results — keep at 4.0, make configurable for Phase 2.
- Model has zero home advantage — host nations (Mexico, USA, Canada) may show false EV signals.
- Overround removal method matters — use proportional (simplest, most common).
- Goal grid truncation at max_goals=10 captures 99.5%+ of probability mass for xG ≤ 4.0.
- Degenerate xG (λ=0.0 for very weak teams like Curaçao) requires floor at 1e-6.

### Metis Review
**Identified Gaps** (addressed):
- **Clean xG extraction strategy**: Resolved — Option C (add `team_a_clean_xg`/`team_b_clean_xg` keys to `predict_match()` return dict). Backward-compatible, no API breakage.
- **Poisson dependency**: Resolved — pure Python implementation (`e^(-λ) * λ^k / k!`), no scipy import.
- **Goal grid truncation**: Resolved — `max_goals=10` with tail mass verification < 0.001.
- **Degenerate xG floor**: Resolved — λ floored at 1e-6.
- **Overround method**: Resolved — proportional normalization.
- **Kelly validation**: Resolved — odds > 1.01 minimum, 5% bankroll hard cap, odds ≤ 1 rejected.
- **Phase 1 market scope**: Resolved — 1X2 + Totals + BTTS (all derivable from the same Poisson grid).
- **Knockout exclusion**: Resolved — Phase 1 explicitly group-stage only.

---

## Work Objectives

### Core Objective
Build an MVP football betting pipeline that converts the existing World Cup 2026 xG model into calibrated match-outcome probabilities, compares them against Bet365 odds (via manual CSV), and outputs positive-EV bet candidates with fractional-Kelly stake sizing — enabling paper betting on the current tournament's group stage.

### Concrete Deliverables
- `src/predict.py` — extended with `team_a_clean_xg` / `team_b_clean_xg` fields
- `src/betting/__init__.py` — package init
- `src/betting/probabilities.py` — pure-Python Poisson PMF + 1X2/Totals/BTTS calculators
- `src/betting/odds.py` — CSV odds parser, provider interface, overround removal
- `src/betting/selector.py` — EV calculator + quarter-Kelly staking engine
- `src/betting/ledger.py` — append-only paper bet ledger (CSV)
- `src/betting/validation.py` — odds validation + team name resolution
- `src/betting/cli.py` — CLI entry point for betting pipeline
- `tests/betting/__init__.py`
- `tests/betting/test_probabilities.py` — ≥6 test functions (golden, edge, degenerate)
- `tests/betting/test_odds.py` — ≥5 test functions (parsing, validation, overround)
- `tests/betting/test_selector.py` — ≥5 test functions (EV, Kelly, caps)
- `tests/betting/test_ledger.py` — ≥4 test functions (schema, append, empty, sequential)
- `tests/betting/test_validation.py` — ≥4 test functions
- `tests/betting/test_cli.py` — ≥2 integration tests
- `tests/betting/conftest.py` — shared fixtures
- `tests/fixtures/sample_odds.csv` — valid test odds file
- `tests/fixtures/sample_odds_invalid.csv` — error-case odds file
- `output/betting/` — output directory for ledger CSV

### Definition of Done
- [x] `python -m pytest tests/ -v` → ALL existing + new tests pass (0 failures)
- [x] `python -m src.betting.cli --odds tests/fixtures/sample_odds.csv --no-fetch --bankroll 1000 --output-dir /tmp/betting_test` → exit 0, paper_bet_ledger.csv exists with rows
- [x] Regressions: all existing tests in `tests/test_*.py` pass unchanged
- [x] `python -m src.cli --seed 42 --no-fetch` still works identically to before

### Must Have
- Clean xG values accessible from prediction pipeline (no noise for probability calc)
- Poisson 1X2 probabilities summing to 1.0 ± 0.0001 for any valid xG pair
- Odds CSV parser handling UTF-8 team names (Côte d'Ivoire, Türkiye, Curaçao)
- Proportional overround normalization (no-vig implied probabilities)
- EV calculation: `p_model * odds - 1`
- Quarter-Kelly staking: `0.25 * edge / (odds - 1)` with 5% bankroll cap
- Append-only paper bet ledger CSV with complete audit trail
- CLI prints ranked bet candidates with: match, market, selection, odds, model prob, market prob, edge, EV, Kelly, stake, decision

### Must NOT Have (Guardrails)
- **NO scraping of Bet365** — manual CSV input only
- **NO modification of**: `src/formula.py`, `src/aggregate.py`, `src/schedule.py`, `src/fifa_data.py`, `src/country_map.py`
- **NO scipy dependency** — pure Python Poisson
- **NO Dixon-Coles adjustment** — deferred to Phase 2
- **NO DNB or Asian handicap markets** — deferred to Phase 2
- **NO model calibration or backtesting** — deferred to Phase 2
- **NO web dashboard, visualization, or API** — CLI only
- **NO knockout-stage prediction** — group stage only
- **NO multi-bookmaker support** — single `CsvOddsProvider`
- **NO live odds fetching** — manual input only
- **NO accumulators/parlays** — singles only
- **NO probability calibration** (Brier, reliability curves) — deferred to Phase 2
- **NO Elo, SPI, squad-value, or injury features** — deferred to Phase 2

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES — pytest with 14 existing test modules
- **Automated tests**: TDD — RED (failing test) → GREEN (minimal impl) → REFACTOR
- **Framework**: pytest (already configured in `pyproject.toml`)
- **Every task follows**: Write test → verify RED → implement → verify GREEN → refactor

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI**: Use Bash — Run command, assert exit code + output content + ledger file existence
- **Math modules**: Use Bash (python REPL) — Import module, call function, assert return value
- **CSV output**: Use Bash — Parse CSV, assert column count, row count, specific values

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation: 4 tasks, ALL parallel):
├── Task 1: Clean xG extraction in predict.py [quick]
├── Task 2: Poisson probability math module [quick]
├── Task 4: Validation module + team name resolution [quick]
└── Task 5: Odds CSV parser + provider interface [quick]

Wave 2a (After Wave 1 — market models: 3 tasks, ALL parallel):
├── Task 3: 1X2 market probability calculator (depends: 2) [quick]
├── Task 6: Totals + BTTS market calculators (depends: 2) [quick]
└── Task 7: Overround removal + market normalization (depends: 4, 5) [quick]

Wave 2b (After Wave 2a — betting math, sequential):
├── Task 8: EV calculator + bet selector (depends: 3, 6, 7) [quick]
└── Task 9: Kelly staking engine with caps (depends: 8) [quick]

Wave 3 (After Wave 2b — integration + output: 3 tasks, sequential):
├── Task 10: Paper bet ledger CSV (depends: 9) [quick]
├── Task 11: Betting CLI entry point (depends: 1, 5, 8, 10) [unspecified-high]
└── Task 12: End-to-end integration test + fixtures (depends: 11) [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit [oracle]
├── Task F2: Code quality review [unspecified-high]
├── Task F3: Real manual QA [unspecified-high]
└── Task F4: Scope fidelity check [deep]

Critical Path: Task 1 → Task 2 → Task 3 → Task 8 → Task 9 → Task 10 → Task 11 → F1-F4 → user okay
Parallel Speedup: ~50% faster than sequential (Wave 1 runs 4 tasks simultaneously; Wave 2a runs 3)
Max Concurrent: 4 (Wave 1)
```

### Dependency Matrix

- **1**: - - 11, 3
- **2**: - - 3, 6, 2a
- **3**: 2 - 8, 2a
- **4**: - - 7, 1
- **5**: - - 7, 11, 1
- **6**: 2 - 8, 2a
- **7**: 4, 5 - 8, 2a
- **8**: 3, 6, 7 - 9, 11, 2b
- **9**: 8 - 10, 2b
- **10**: 9 - 11, 3
- **11**: 1, 5, 8, 10 - 12, 3
- **12**: 11 - -, 3
- **F1-F4**: all tasks complete - -, FINAL

### Agent Dispatch Summary

- **Wave 1**: **4** — T1, T2, T4, T5 all → `quick`
- **Wave 2a**: **3** — T3→`quick`, T6→`quick`, T7→`quick`
- **Wave 2b**: **2** — T8→`quick`, T9→`quick` (sequential)
- **Wave 3**: **3** — T10→`quick`, T11→`unspecified-high`, T12→`quick`
- **FINAL**: **4** — F1→`oracle`, F2→`unspecified-high`, F3→`unspecified-high`, F4→`deep`

---

## TODOs

- [x] 1. Clean xG extraction — add noise-free xG to `predict_match()` return dict

  **What to do**:
  - In `src/predict.py`, inside `predict_match()`, compute `team_a_clean_xg = blended_to_xg(a_blended)` and `team_b_clean_xg = blended_to_xg(b_blended)` BEFORE the noise is applied
  - Add `"team_a_clean_xg": team_a_clean_xg` and `"team_b_clean_xg": team_b_clean_xg` keys to the return dict
  - This is backward-compatible — existing callers ignore unknown keys
  - Add a new test in `tests/betting/test_predict_ext.py` (or add to existing `tests/test_predict.py`) that verifies clean_xg ≠ noisy_xg when seed is provided, and that clean_xg values equal `blended_to_xg(blended_score)` exactly
  - Run existing test suite to confirm zero regressions: `python -m pytest tests/ -v --ignore=tests/betting/`

  **Must NOT do**:
  - Do NOT modify `apply_noise()` or `compute_blended_score()`
  - Do NOT change existing return dict keys
  - Do NOT change the function signature of `predict_match()`
  - Do NOT add scipy or any new dependency

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single function modification, ~5 lines of new code, backward-compatible addition
  - **Skills**: None required
  - **Skills Evaluated but Omitted**: N/A

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: Task 11 (CLI needs clean xG)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `src/predict.py:102-112` — The `predict_match()` function where clean xG must be extracted. Note how `a_blended` and `b_blended` are computed on lines 102-103 but only the noisy xG (lines 108-112) is stored. Insert clean xG computation between lines 103 and 105 (before `apply_noise`).
  - `src/predict.py:29-31` — `blended_to_xg()` function: `blended * 4.0`. This is the formula to replicate for clean xG.
  - `tests/test_predict.py` — Existing test patterns to follow: assert dict keys, assert float values within tolerance.
  - `src/predict.py:55-128` — Full `predict_match()` function signature and return dict structure for reference.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_predict_ext.py` created with `test_clean_xg_present` and `test_clean_xg_no_noise`
  - [ ] `python -m pytest tests/betting/test_predict_ext.py -v` → PASS (2+ tests)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Clean xG equals blended * 4 (no noise)
    Tool: Bash
    Preconditions: pytest installed, src/predict.py modified
    Steps:
      1. Run: python -c "from src.predict import blended_to_xg; print(blended_to_xg(0.75))"
      2. Assert output is exactly "3.0"
    Expected Result: 3.0 (blended * 4 = 0.75 * 4 = 3.0)
    Failure Indicators: Any value other than 3.0
    Evidence: .omo/evidence/task-1-clean-xg-formula.txt

  Scenario: predict_match returns both clean and noisy xG
    Tool: Bash
    Preconditions: Mock dataset with two teams, seed=42
    Steps:
      1. Run: python -c "
    from src.predict import predict_match
    import pandas as pd
    df = pd.DataFrame([{'iso3':'FRA','norm_fifa':0.9,'norm_econ':0.8,'econ_score':2.5,'fifa_points':1800},
                        {'iso3':'CPV','norm_fifa':0.1,'norm_econ':0.0,'econ_score':0.0,'fifa_points':900}])
    result = predict_match('FRA','CPV',df,seed=42)
    print('clean_xg keys:', 'team_a_clean_xg' in result, 'team_b_clean_xg' in result)
    print('clean_a:', result.get('team_a_clean_xg'))
    print('noisy_a:', result.get('team_a_xg'))
    print('different:', abs(result['team_a_clean_xg'] - result['team_a_xg']) > 0.01)
    "
      2. Assert output contains "clean_xg keys: True True"
      3. Assert output contains "different: True" (noise makes values differ)
    Expected Result: Clean xG keys present, clean ≠ noisy
    Failure Indicators: Missing keys, clean equals noisy
    Evidence: .omo/evidence/task-1-clean-vs-noisy.txt
  ```

  **Commit**: YES (groups with Tasks 2, 4, 5 in Wave 1)
  - Message: `feat(betting): add clean xG extraction to predict_match() return dict`
  - Files: `src/predict.py`, `tests/betting/test_predict_ext.py`

- [x] 2. Poisson probability math module — pure Python Poisson PMF

  **What to do**:
  - Create `src/betting/__init__.py` (empty)
  - Create `src/betting/probabilities.py` with `poisson_pmf(k, lam)` function:
    ```python
    import math
    def poisson_pmf(k: int, lam: float) -> float:
        if lam <= 0:
            lam = 1e-6  # floor for degenerate xG
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
    ```
  - Create `poisson_probs(lam, max_goals=10)` that returns list of P(k) for k=0..max_goals
  - Include `validate_tail_mass(probs)` that asserts remaining tail mass < 0.001
  - Create `tests/betting/__init__.py` (empty) and `tests/betting/conftest.py` with shared fixtures
  - Create `tests/betting/test_probabilities.py` with:
    - `test_poisson_pmf_sum_to_one` — sum of `poisson_probs(2.0, 10)` ≈ 1.0
    - `test_poisson_pmf_zero_k` — `poisson_pmf(0, 2.0)` ≈ 0.1353 (e^-2)
    - `test_degenerate_low_xg` — `poisson_probs(0.0)` doesn't raise, P(k=0) ≈ 1.0
    - `test_degenerate_high_xg` — `poisson_probs(4.0, 10)` tail mass < 0.001
    - `test_tail_mass_validation` — `validate_tail_mass` raises when tail > 0.01
    - `test_negative_lam` — negative lambda is floored to 1e-6

  **Must NOT do**:
  - Do NOT import scipy or any external statistics library
  - Do NOT use numpy

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure math functions, ~40 lines of code, well-defined formulas
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: Tasks 3, 6 (market calculators depend on Poisson engine)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `src/formula.py` — Existing module pattern: pure Python, math imports, type hints, numpy-free
  - `tests/test_formula.py` — Existing test pattern: pytest functions (not classes), `from __future__ import annotations`
  - `pyproject.toml:49-58` — pytest configuration: testpaths, python_files, python_classes, python_functions
  - Poisson PMF formula: `P(X=k) = e^(-λ) * λ^k / k!`

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_probabilities.py` created with 6 test functions
  - [ ] `python -m pytest tests/betting/test_probabilities.py -v` → PASS (6 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Poisson PMF golden values match known math
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import poisson_pmf
    import math
    p0 = poisson_pmf(0, 2.0)
    expected = math.exp(-2.0)
    print(f'P(0|2.0)={p0:.6f}, expected={expected:.6f}, match={abs(p0-expected)<1e-10}')
    "
      2. Assert output contains "match=True"
    Expected Result: P(0|λ=2.0) = e^(-2.0) ≈ 0.135335
    Failure Indicators: Mismatch with known value
    Evidence: .omo/evidence/task-2-poisson-golden.txt

  Scenario: Degenerate xG (λ=0.0) doesn't break
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import poisson_probs
    probs = poisson_probs(0.0, max_goals=10)
    print(f'num_probs={len(probs)}, P(0)={probs[0]:.6f}, sum={sum(probs):.6f}')
    "
      2. Assert output shows P(0) > 0.99 and sum > 0.99
    Expected Result: Probabilities sum to near 1.0, no NaN, no exception
    Failure Indicators: Exception, NaN, sum far from 1.0
    Evidence: .omo/evidence/task-2-degenerate-xg.txt
  ```

  **Commit**: YES (groups with Tasks 1, 4, 5 in Wave 1)
  - Message: `feat(betting): add pure Python Poisson probability math module`
  - Files: `src/betting/__init__.py`, `src/betting/probabilities.py`, `tests/betting/__init__.py`, `tests/betting/conftest.py`, `tests/betting/test_probabilities.py`

- [x] 3. 1X2 market probability calculator — Home/Draw/Away from Poisson grid

  **What to do**:
  - Add to `src/betting/probabilities.py`:
    - `match_outcome_probs(xg_home, xg_away, max_goals=10)` returning dict `{"home": p, "draw": p, "away": p}`
    - Algorithm: build outer-product matrix of P(home=i) × P(away=j) for i,j in [0..max_goals]
    - `p_home = Σ P(i,j) for i > j`, `p_draw = Σ P(i,j) for i == j`, `p_away = Σ P(i,j) for i < j`
    - Verify probabilities sum to 1.0 ± 0.0001
  - Add tests to `tests/betting/test_probabilities.py`:
    - `test_1x2_golden` — (xg_h=2.0, xg_a=1.0) → p_home > p_away > p_draw, sum ≈ 1.0
    - `test_1x2_extreme_mismatch` — (xg_h=4.0, xg_a=0.0) → p_home > 0.95
    - `test_1x2_balanced` — (xg_h=2.0, xg_a=2.0) → p_home ≈ p_away, p_draw ≈ 0.28
    - `test_1x2_prob_sum` — for any valid xG pair, abs(sum - 1.0) < 0.001

  **Must NOT do**:
  - Do NOT apply noise — use clean xG
  - Do NOT add Dixon-Coles correlation adjustment
  - Do NOT use any external library for the matrix computation

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Extends existing module, pure math, ~30 lines, well-defined algorithm
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2a (with Tasks 6, 7)
  - **Blocks**: Task 8 (EV calculator needs 1X2 probs)
  - **Blocked By**: Task 2 (needs Poisson engine)

  **References**:
  - `src/betting/probabilities.py` (Task 2 output) — `poisson_probs()` function to build the grid from
  - Outer-product algorithm: For each (i, j) pair where i = home goals, j = away goals: `prob = poisson_probs_home[i] * poisson_probs_away[j]`, accumulate into home/draw/away buckets based on i > j, i == j, i < j

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test functions in `tests/betting/test_probabilities.py`: `test_1x2_golden`, `test_1x2_extreme_mismatch`, `test_1x2_balanced`, `test_1x2_prob_sum`
  - [ ] `python -m pytest tests/betting/test_probabilities.py -v` → all tests pass

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: 1X2 golden test — Brazil vs Scotland (xg_h=2.8, xg_a=0.6)
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import match_outcome_probs
    probs = match_outcome_probs(2.8, 0.6)
    print(f'home={probs[\"home\"]:.4f} draw={probs[\"draw\"]:.4f} away={probs[\"away\"]:.4f} sum={probs[\"home\"]+probs[\"draw\"]+probs[\"away\"]:.4f}')
    "
      2. Assert p_home > 0.65 (strong favorite)
      3. Assert p_away < 0.10 (big underdog)
      4. Assert sum is 1.0 ± 0.001
    Expected Result: p_home ~ 0.72, p_draw ~ 0.20, p_away ~ 0.08
    Failure Indicators: Sum ≠ 1.0, p_home < p_away, NaN
    Evidence: .omo/evidence/task-3-1x2-golden.txt

  Scenario: Balanced match — identical xG produces near-symmetric probs
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import match_outcome_probs
    probs = match_outcome_probs(2.0, 2.0)
    print(f'home={probs[\"home\"]:.4f} draw={probs[\"draw\"]:.4f} away={probs[\"away\"]:.4f}')
    print(f'symmetric={abs(probs[\"home\"]-probs[\"away\"]) < 0.001}')
    "
      2. Assert p_home ≈ p_away (within 0.001)
    Expected Result: p_home ≈ 0.36, p_draw ≈ 0.28, p_away ≈ 0.36
    Failure Indicators: Large asymmetry when xG is equal
    Evidence: .omo/evidence/task-3-1x2-balanced.txt
  ```

  **Commit**: YES (groups with Tasks 6, 7 in Wave 2a)
  - Message: `feat(betting): add 1X2 match outcome probability calculator`
  - Files: `src/betting/probabilities.py`, `tests/betting/test_probabilities.py`

- [x] 4. Validation module — odds validation + team name resolution

  **What to do**:
  - Create `src/betting/validation.py`:
    - `resolve_team_name(name: str) -> str`: Map FIFA display names ("England", "Ivory Coast", "South Korea") to ISO3 codes ("GBR", "CIV", "KOR")
    - Build a `TEAM_ALIASES` dict from `COUNTRY_MAP` entries: for each country, map all known name variants (FIFA name, common English name, alternative names) to its ISO3
    - `validate_odds_row(row: dict) -> list[str]`: Return list of error messages for a single odds row (empty list = valid)
    - `validate_team_pair(home: str, away: str) -> tuple[str, str]`: Resolve both team names to ISO3, raise `ValueError` with clear message if either fails
  - Create `tests/betting/test_validation.py`:
    - `test_resolve_england` — "England" → "GBR"
    - `test_resolve_ivory_coast` — "Ivory Coast" → "CIV"  
    - `test_resolve_unknown_team` — raises ValueError with team name in message
    - `test_validate_odds_valid` — valid row returns empty error list
    - `test_validate_odds_negative` — odds ≤ 0 returns error
    - `test_validate_odds_missing_field` — missing "home" returns error

  **Must NOT do**:
  - Do NOT modify `src/country_map.py` — build aliases from its data, don't change it
  - Do NOT resolve knockout placeholders ("1A", "W73") — these will be skipped by the calling code

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Mapping + validation, ~60 lines, straightforward logic
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: Task 7 (overround removal needs validated team names)
  - **Blocked By**: None (can start immediately — reads COUNTRY_MAP at module level)

  **References**:
  - `src/country_map.py` — The `COUNTRY_MAP` list of dicts. Each entry has: `"iso3"`, `"name"` (FIFA name), `"code"`. Extract name→iso3 mappings from here.
  - `src/schedule.py:28-104` — The `_GROUP_MATCHES` list shows FIFA team names as used in the schedule (e.g., "England", "Côte d'Ivoire", "Korea Republic", "IR Iran"). These are the names odds CSV may contain.
  - `src/cli.py:239-258` — `_convert_match_to_iso3()` function: existing pattern for resolving team names to ISO3 using `get_iso3()`. Your validation module should use the same mapping.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_validation.py` created with 6 test functions
  - [ ] `python -m pytest tests/betting/test_validation.py -v` → PASS (6 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: All 48 World Cup team names resolve to valid ISO3
    Tool: Bash
    Preconditions: Module importable, COUNTRY_MAP loaded
    Steps:
      1. Run: python -c "
    from src.betting.validation import resolve_team_name
    from src.schedule import MATCHES
    teams = set()
    for m in MATCHES:
        if m['status'] != 'knockout':
            teams.add(m['team_a'])
            teams.add(m['team_b'])
    failed = []
    for t in sorted(teams):
        try:
            iso3 = resolve_team_name(t)
        except ValueError:
            failed.append(t)
    print(f'total_teams={len(teams)}, failed={len(failed)}')
    if failed: print(f'FAILED: {failed}')
    "
      2. Assert failed=0 (all 48 group-stage teams resolve)
    Expected Result: 48 team names all map to ISO3, zero failures
    Failure Indicators: Any team name fails to resolve
    Evidence: .omo/evidence/task-5-team-resolution.txt

  Scenario: Invalid odds row returns specific errors
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.validation import validate_odds_row
    bad_row = {'decimal_odds': '-1.5', 'home': 'France', 'away': 'Brazil'}
    errors = validate_odds_row(bad_row)
    print(f'errors={errors}')
    print(f'has_error={len(errors) > 0}')
    "
      2. Assert errors list is non-empty
      3. Assert at least one error mentions "odds" or "decimal"
    Expected Result: Errors list contains specific message about invalid odds
    Failure Indicators: Empty error list for known-bad input
    Evidence: .omo/evidence/task-5-validation-errors.txt
  ```

  **Commit**: YES (groups with Tasks 1, 2, 4 in Wave 1)
  - Message: `feat(betting): add odds validation and team name resolution module`
  - Files: `src/betting/validation.py`, `tests/betting/test_validation.py`

- [x] 5. Odds CSV parser + provider interface — ingest Bet365 odds from CSV

  **What to do**:
  - Create `src/betting/odds.py`:
    - Define `OddsProvider` protocol/ABC with `fetch_odds() -> list[dict]` method
    - Implement `CsvOddsProvider` class:
      - Constructor takes `csv_path: Path`
      - `fetch_odds()` reads CSV, validates columns, returns list of odds dicts
      - CSV schema: `timestamp, event_id, kickoff, home, away, book, market, selection, line, decimal_odds`
      - Handle UTF-8 encoding (BOM, international team names)
      - Convert `decimal_odds` to float, validate > 1.01
    - `validate_odds_csv(csv_path)` function that checks: headers present, all decimal_odds valid, no missing required fields, reports ALL errors at once
  - Create `tests/betting/test_odds.py`:
    - `test_parse_valid_csv` — parses without errors, returns correct count
    - `test_missing_header` — clear error message
    - `test_invalid_odds_value` — validation catches odds ≤ 1.0
    - `test_encoding_utf8` — handles Côte d'Ivoire, Türkiye
    - `test_empty_csv` — handles gracefully
  - Create `tests/fixtures/sample_odds.csv` — valid 5-match odds CSV
  - Create `tests/fixtures/sample_odds_invalid.csv` — CSV with errors (missing header, bad odds)

  **Must NOT do**:
  - Do NOT scrape Bet365 or any website
  - Do NOT implement API-based odds providers (deferred to Phase 2)
  - Do NOT import aiohttp, httpx, or any HTTP client

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: CSV parsing + validation, ~80 lines, well-defined schema
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: Tasks 7, 11 (overround removal and CLI need odds parser)
  - **Blocked By**: None (can start immediately)

  **References**:
  - `src/output.py:96-106` — Existing CSV writing pattern: `csv.DictWriter`, `newline=""`, `encoding="utf-8"`. Mirror this for reading.
  - `src/cli.py:64-76` — Existing validation pattern: `_valid_iso_date()` type validator. Follow this style for odds validation.
  - `src/country_map.py` — Team name mapping. The odds CSV may use "England" (FIFA name) but the model uses "GBR" (ISO3). Task 5 handles resolution.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_odds.py` created with 5 test functions
  - [ ] `python -m pytest tests/betting/test_odds.py -v` → PASS (5 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Valid CSV parses correctly
    Tool: Bash
    Preconditions: tests/fixtures/sample_odds.csv exists
    Steps:
      1. Run: python -c "
    from src.betting.odds import CsvOddsProvider
    provider = CsvOddsProvider('tests/fixtures/sample_odds.csv')
    odds = provider.fetch_odds()
    print(f'rows={len(odds)}, has_headers={all(k in odds[0] for k in [\"home\",\"away\",\"decimal_odds\"])}')
    "
      2. Assert rows > 0 and has_headers=True
    Expected Result: Parses all rows, all required fields present
    Failure Indicators: Zero rows, missing fields, UnicodeDecodeError
    Evidence: .omo/evidence/task-4-parse-valid.txt

  Scenario: Invalid CSV is caught with clear error
    Tool: Bash
    Preconditions: tests/fixtures/sample_odds_invalid.csv exists
    Steps:
      1. Run: python -c "
    from src.betting.odds import validate_odds_csv
    try:
        validate_odds_csv('tests/fixtures/sample_odds_invalid.csv')
    except ValueError as e:
        print(f'ERROR: {e}')
    "
      2. Assert output contains "ERROR:" with descriptive message
    Expected Result: ValueError raised with specific field name and reason
    Failure Indicators: Generic error, no error raised, silent pass
    Evidence: .omo/evidence/task-4-parse-invalid.txt
  ```

  **Commit**: YES (groups with Tasks 1, 2, 5 in Wave 1)
  - Message: `feat(betting): add odds CSV parser with provider interface`
  - Files: `src/betting/odds.py`, `tests/betting/test_odds.py`, `tests/fixtures/sample_odds.csv`, `tests/fixtures/sample_odds_invalid.csv`

- [x] 6. Totals + BTTS market calculators — Over/Under 2.5 and Both Teams To Score

  **What to do**:
  - Add to `src/betting/probabilities.py`:
    - `totals_probs(xg_home, xg_away, line=2.5, max_goals=10) -> dict`: 
      - Total goals distribution = Poisson(xg_home + xg_away) for each k
      - `p_over = Σ P(total > line)`, `p_under = Σ P(total < line)`
      - Since Poisson is discrete and line=2.5, no push possible
    - `btts_probs(xg_home, xg_away, max_goals=10) -> dict`:
      - `p_home_score = 1 - e^(-xg_home)`, `p_away_score = 1 - e^(-xg_away)`
      - `p_btts_yes = p_home_score * p_away_score` (independence assumption)
      - `p_btts_no = 1 - p_btts_yes`
    - Document independence assumption in docstring
  - Add tests to `tests/betting/test_probabilities.py`:
    - `test_totals_over_25` — (xg_h=2.0, xg_a=1.5) → p_over > p_under
    - `test_totals_under_25` — (xg_h=0.5, xg_a=0.5) → p_under > p_over
    - `test_btts_high_xg` — (xg_h=2.0, xg_a=2.0) → p_btts > 0.70
    - `test_btts_low_xg` — (xg_h=0.1, xg_a=0.1) → p_btts < 0.05
    - `test_btts_sum_to_one` — btts_yes + btts_no ≈ 1.0

  **Must NOT do**:
  - Do NOT apply Dixon-Coles correlation adjustment
  - Do NOT support non-standard over/under lines (1.5, 3.5) — only 2.5 for MVP

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Two trivial derivations from existing Poisson engine, ~20 lines
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 7; both depend on Wave 1 but not each other)
  - **Blocks**: Task 8 (EV calculator needs totals + BTTS probs)
  - **Blocked By**: Task 2 (needs Poisson engine)

  **References**:
  - `src/betting/probabilities.py` (Task 2 output) — `poisson_probs()` and `poisson_pmf()` functions
  - Totals formula: The sum of two independent Poisson(λ₁) and Poisson(λ₂) is Poisson(λ₁+λ₂). So `poisson_pmf(k, xg_home + xg_away)` gives P(total = k).
  - BTTS formula: P(home scores ≥ 1) = 1 - P(home = 0) = 1 - e^(-λ_home). Independence: P(both score) = P(home≥1) × P(away≥1).

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test functions added to `tests/betting/test_probabilities.py`: 5 new functions
  - [ ] `python -m pytest tests/betting/test_probabilities.py -v` → all tests pass

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: High-scoring match leans over 2.5
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import totals_probs
    probs = totals_probs(2.0, 1.5)
    print(f'over={probs[\"over\"]:.4f} under={probs[\"under\"]:.4f} sum={probs[\"over\"]+probs[\"under\"]:.4f}')
    print(f'over_gt_under={probs[\"over\"] > probs[\"under\"]}')
    "
      2. Assert over > under (total xG = 3.5 > 2.5 line)
      3. Assert sum ≈ 1.0
    Expected Result: p_over ≈ 0.60-0.70, p_under ≈ 0.30-0.40
    Failure Indicators: over < under, sum ≠ 1.0
    Evidence: .omo/evidence/task-6-totals-over.txt

  Scenario: BTTS is near certain when both xG are high
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.probabilities import btts_probs
    probs = btts_probs(2.5, 2.0)
    print(f'yes={probs[\"yes\"]:.4f} no={probs[\"no\"]:.4f} sum={probs[\"yes\"]+probs[\"no\"]:.4f}')
    "
      2. Assert btts_yes > 0.75
      3. Assert sum ≈ 1.0
    Expected Result: btts_yes ≈ 0.80-0.90
    Failure Indicators: btts_yes < 0.5, sum ≠ 1.0
    Evidence: .omo/evidence/task-6-btts-high.txt
  ```

  **Commit**: YES (groups with Tasks 3, 7 in Wave 2a)
  - Message: `feat(betting): add totals O/U 2.5 and BTTS market calculators`
  - Files: `src/betting/probabilities.py`, `tests/betting/test_probabilities.py`

- [x] 7. Overround removal — bookmaker margin normalization

  **What to do**:
  - Add to `src/betting/odds.py`:
    - `remove_overround(odds_by_selection: dict[str, float]) -> dict[str, float]`:
      - Compute raw implied probs: `raw = {k: 1/v for k, v in odds_by_selection.items()}`
      - Total overround: `total = sum(raw.values())`
      - Normalized: `{k: p/total for k, p in raw.items()}`
      - Validate sum is 1.0 ± 0.0001
    - `market_implied_probs(odds_rows: list[dict], market: str) -> dict`: Group odds rows by event_id + market, apply overround removal, return structured dict of normalized implied probabilities per event per selection
  - Add tests to `tests/betting/test_odds.py`:
    - `test_remove_overround_1x2` — odds [2.0, 3.5, 4.0] → implied probs sum to 1.0
    - `test_remove_overround_no_overround` — odds [2.0, 2.0] (fair 2-way market) → probs are [0.5, 0.5]
    - `test_remove_overround_heavy_margin` — odds [1.5, 3.0, 6.0] → probs still sum to 1.0

  **Must NOT do**:
  - Do NOT implement multiplicative, Shin, or other overround methods — proportional only
  - Do NOT handle markets with pushes (Asian handicap) — 1X2/totals only

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple arithmetic, ~30 lines, well-defined math
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 6; both depend on Wave 1 but not each other)
  - **Blocks**: Task 8 (EV calculator needs no-vig probabilities)
  - **Blocked By**: Tasks 4, 5 (needs parsed odds and validated team names)

  **References**:
  - `src/betting/odds.py` (Task 4 output) — `CsvOddsProvider` and its output format
  - `src/betting/validation.py` (Task 5 output) — `resolve_team_name()` for matching odds rows to model data
  - Proportional overround formula: `no_vig_prob_i = (1/odds_i) / Σ(1/odds_j)` for all j in the market

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test functions added to `tests/betting/test_odds.py`: 3 new functions
  - [ ] `python -m pytest tests/betting/test_odds.py -v` → all tests pass

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: 1X2 overround removal sum equals 1.0
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.odds import remove_overround
    odds = {'home': 2.10, 'draw': 3.40, 'away': 3.60}
    probs = remove_overround(odds)
    total = sum(probs.values())
    raw = {k: 1/v for k,v in odds.items()}
    print(f'raw_sum={sum(raw.values()):.4f} no_vig_sum={total:.4f} valid={abs(total-1.0)<0.0001}')
    print(f'home={probs[\"home\"]:.4f} draw={probs[\"draw\"]:.4f} away={probs[\"away\"]:.4f}')
    "
      2. Assert raw_sum > 1.0 (overround exists)
      3. Assert no_vig_sum = 1.0 ± 0.0001
      4. Assert home > draw > away (logical ordering)
    Expected Result: Raw sum ≈ 1.048, no-vig sum = 1.0
    Failure Indicators: no-vig sum ≠ 1.0, probs not in logical order
    Evidence: .omo/evidence/task-7-overround-1x2.txt
  ```

  **Commit**: YES (groups with Tasks 3, 6 in Wave 2a)
  - Message: `feat(betting): add proportional bookmaker overround removal`
  - Files: `src/betting/odds.py`, `tests/betting/test_odds.py`

- [x] 8. EV calculator + bet selector — expected value and bet ranking

  **What to do**:
  - Create `src/betting/selector.py`:
    - `expected_value(p_model: float, decimal_odds: float) -> float`: `p_model * decimal_odds - 1.0`
    - `edge(p_model: float, implied_prob: float) -> float`: `p_model - implied_prob` (percentage points)
    - `select_bets(predictions: list[dict], odds_data: list[dict]) -> list[dict]`:
      - For each match in predictions: get clean xG → compute 1X2 probs
      - Match with odds data by team ISO3 codes
      - Remove overround → compute EV for each selection (home/draw/away)
      - Filter: EV ≥ 0.03 (3% minimum for paper betting; will increase to 5% for Phase 2 live betting), odds between 1.50-3.50
      - Sort by EV descending
      - Return ranked candidates with all metadata
    - `is_candidate(ev: float, odds: float) -> bool`: EV ≥ 0.03 AND 1.50 ≤ odds ≤ 3.50
  - Create `tests/betting/test_selector.py`:
    - `test_ev_positive` — p=0.40, odds=3.00 → EV=0.20
    - `test_ev_negative` — p=0.30, odds=2.00 → EV=-0.40
    - `test_ev_breakeven` — p=0.50, odds=2.00 → EV=0.00
    - `test_edge_percentage` — p=0.55, implied=0.50 → edge=0.05
    - `test_select_bets_filters_negative_ev` — negative EV bets excluded
    - `test_select_bets_empty_input` — returns empty list

  **Must NOT do**:
  - Do NOT implement Kelly staking here — that's Task 9
  - Do NOT modify the prediction model's probabilities

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple formulas + filtering logic, ~60 lines
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential — needs all of Tasks 3, 6, 7)
  - **Blocks**: Tasks 9, 11 (Kelly needs EV, CLI needs bet candidates)
  - **Blocked By**: Tasks 3, 6, 7 (needs 1X2 probs, totals, BTTS, and no-vig odds)

  **References**:
  - `src/betting/probabilities.py` (Tasks 2, 3, 6 output) — `match_outcome_probs()`, `totals_probs()`, `btts_probs()`
  - `src/betting/odds.py` (Tasks 4, 7 output) — `remove_overround()`, `market_implied_probs()`, `CsvOddsProvider`
  - `src/betting/validation.py` (Task 5 output) — `resolve_team_name()`, `validate_team_pair()`
  - EV formula: `EV = p_model × odds − 1`. Positive → profitable in expectation. Negative → avoid.
  - Edge formula: `edge = p_model − implied_prob`. Positive → model thinks team is undervalued.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_selector.py` created with 6 test functions
  - [ ] `python -m pytest tests/betting/test_selector.py -v` → PASS (6 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Positive EV bet passes filter, negative EV bet is excluded
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.selector import expected_value, is_candidate
    good_ev = expected_value(0.55, 2.10)
    bad_ev = expected_value(0.40, 2.10)
    print(f'good_ev={good_ev:.4f} is_candidate={is_candidate(good_ev, 2.10)}')
    print(f'bad_ev={bad_ev:.4f} is_candidate={is_candidate(bad_ev, 2.10)}')
    "
      2. Assert good_ev > 0 and is_candidate=True
      3. Assert bad_ev < 0 and is_candidate=False
    Expected Result: EV(0.55, 2.10) = 0.155 (positive), EV(0.40, 2.10) = -0.16 (negative)
    Failure Indicators: Wrong EV sign, candidate filter incorrect
    Evidence: .omo/evidence/task-8-ev-filter.txt

  Scenario: Low odds (< 1.50) are excluded even with positive EV
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.selector import is_candidate
    result = is_candidate(0.10, 1.30)
    print(f'candidate={result}')
    "
      2. Assert candidate=False (odds 1.30 < 1.50 minimum)
    Expected Result: False — excluded by odds range filter
    Failure Indicators: True — odds filter not applied
    Evidence: .omo/evidence/task-8-odds-filter.txt
  ```

  **Commit**: YES (groups with Task 9 in Wave 2b)
  - Message: `feat(betting): add EV calculator and bet selection engine`
  - Files: `src/betting/selector.py`, `tests/betting/test_selector.py`

- [x] 9. Kelly staking engine — fractional Kelly with hard caps

  **What to do**:
  - Add to `src/betting/selector.py`:
    - `kelly_fraction(p_model: float, decimal_odds: float, fraction: float = 0.25) -> float`:
      - Full Kelly: `edge / (odds - 1.0)` where `edge = p_model * odds - 1.0`
      - Fractional: `fraction * full_kelly`
      - Return 0.0 if edge ≤ 0 or odds ≤ 1
    - `recommend_stake(bankroll: float, p_model: float, decimal_odds: float, fraction: float = 0.25, max_stake_pct: float = 0.05) -> dict`:
      - Compute quarter-Kelly stake
      - Cap at `max_stake_pct * bankroll` (hard 5% cap)
      - Return `{"kelly": full_kelly_value, "stake": capped_stake, "pct_bankroll": stake/bankroll}`
  - Add tests to `tests/betting/test_selector.py`:
    - `test_kelly_golden` — p=0.55, odds=2.00, edge=0.10 → full Kelly=0.10, quarter=0.025
    - `test_kelly_negative_ev` — p=0.40, odds=2.00 → returns 0.0
    - `test_kelly_cap` — edge is huge → stake never exceeds 5% of bankroll
    - `test_kelly_odds_one` — odds=1.0 → returns 0.0 (no division by zero)
    - `test_kelly_odds_below_one` — odds=0.5 → returns 0.0

  **Must NOT do**:
  - Do NOT use full Kelly — always apply fraction (default 0.25)
  - Do NOT allow stake > 5% of bankroll regardless of Kelly
  - Do NOT implement progressive staking or martingale

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple formula with bounds checking, ~30 lines
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential — needs Task 8 EV values)
  - **Blocks**: Task 10 (ledger needs stake recommendations)
  - **Blocked By**: Task 8 (needs EV calculator)

  **References**:
  - `src/betting/selector.py` (Task 8 output) — `expected_value()` function
  - Kelly formula: `f* = (p * b - q) / b` where b = decimal_odds - 1 (net odds), q = 1 - p. Simplified: `f* = (p * odds - 1) / (odds - 1)`.
  - Quarter Kelly: `stake = bankroll * 0.25 * f*`
  - Hard cap: `stake = min(stake, bankroll * 0.05)`

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test functions added to `tests/betting/test_selector.py`: 5 new functions
  - [ ] `python -m pytest tests/betting/test_selector.py -v` → all tests pass

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Quarter Kelly cap is enforced
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -c "
    from src.betting.selector import recommend_stake
    # Very high edge scenario: p=0.95, odds=1.50
    # Full Kelly = (0.95*1.50 - 1)/(1.50-1) = (0.425)/(0.5) = 0.85
    # Quarter Kelly = 0.2125 → stake would be 21.25% bankroll
    # Cap at 5% → 50.00
    result = recommend_stake(1000.0, 0.95, 1.50)
    print(f'kelly={result[\"kelly\"]:.4f} stake={result[\"stake\"]:.2f} pct={result[\"pct_bankroll\"]:.4f}')
    print(f'capped={result[\"stake\"] <= 50.0}')
    "
      2. Assert stake ≤ 50.0 (5% of 1000)
      3. Assert pct_bankroll ≤ 0.05
    Expected Result: Stake capped at 50.00 regardless of Kelly value
    Failure Indicators: Stake exceeds 5% cap
    Evidence: .omo/evidence/task-9-kelly-cap.txt
  ```

  **Commit**: YES (groups with Task 8 in Wave 2b)
  - Message: `feat(betting): add fractional Kelly staking engine with 5% cap`
  - Files: `src/betting/selector.py`, `tests/betting/test_selector.py`

- [x] 10. Paper bet ledger — append-only CSV with audit trail

  **What to do**:
  - Create `src/betting/ledger.py`:
    - `LEDGER_COLUMNS` constant: `["timestamp", "event_id", "match_date", "team_a", "team_b", "market", "selection", "model_prob", "implied_prob", "decimal_odds", "edge", "ev", "kelly", "stake", "bankroll_before", "bankroll_after", "status"]`
    - `init_ledger(output_path: Path) -> Path`: Create CSV file with header row if it doesn't exist, return path
    - `log_bet(output_path: Path, bet: dict, bankroll: float) -> dict`: Append one row, compute `bankroll_after = bankroll - stake`, return updated bankroll
    - `log_bets(output_path: Path, bets: list[dict], bankroll: float) -> float`: Log multiple bets sequentially, return final bankroll
    - `read_ledger(output_path: Path) -> list[dict]`: Read entire ledger back as list of dicts
  - Create `tests/betting/test_ledger.py`:
    - `test_init_ledger` — creates file with header row only
    - `test_log_single_bet` — appends one row, bankroll updates correctly
    - `test_log_multiple_bets` — sequential bets, running bankroll tracked
    - `test_read_empty_ledger` — header only, 0 data rows
    - `test_ledger_schema` — all 17 columns present in header

  **Must NOT do**:
  - Do NOT use a database — CSV only for MVP
  - Do NOT track actual results or P&L — paper betting (status always "pending")

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: CSV append logic, ~50 lines, straightforward
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential — needs Task 9 stake values)
  - **Blocks**: Task 11 (CLI writes to ledger)
  - **Blocked By**: Task 9 (needs Kelly stake recommendations)

  **References**:
  - `src/output.py:96-106` — Existing CSV pattern: `csv.DictWriter`, encoding, `newline=""`. Follow this exact style.
  - `src/output.py:24-39` — `CSV_COLUMNS` constant pattern. Use same approach for `LEDGER_COLUMNS`.
  - Invest-alchemy ledger pattern (from librarian): append-only CSV, running balance in each row, timestamp on every entry.

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_ledger.py` created with 5 test functions
  - [ ] `python -m pytest tests/betting/test_ledger.py -v` → PASS (5 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Sequential bets update bankroll correctly
    Tool: Bash
    Preconditions: Module importable, temp directory exists
    Steps:
      1. Run: python -c "
    import tempfile, os
    from pathlib import Path
    from src.betting.ledger import init_ledger, log_bets
    tmp = Path(tempfile.mkdtemp())
    ledger_path = tmp / 'test_ledger.csv'
    init_ledger(ledger_path)
    bets = [
        {'timestamp': '2026-06-15', 'event_id': 'WC2026-13', 'match_date': '2026-06-15',
         'team_a': 'ESP', 'team_b': 'CPV', 'market': '1X2', 'selection': 'ESP',
         'model_prob': 0.82, 'implied_prob': 0.80, 'decimal_odds': 1.25, 'edge': 0.02,
         'ev': 0.025, 'kelly': 0.02, 'stake': 5.0, 'bankroll_before': 1000, 'status': 'candidate'},
        {'timestamp': '2026-06-15', 'event_id': 'WC2026-15', 'match_date': '2026-06-15',
         'team_a': 'SAU', 'team_b': 'URY', 'market': '1X2', 'selection': 'URY',
         'model_prob': 0.45, 'implied_prob': 0.38, 'decimal_odds': 2.60, 'edge': 0.07,
         'ev': 0.17, 'kelly': 0.04, 'stake': 15.0, 'bankroll_before': 995, 'status': 'candidate'},
    ]
    final = log_bets(ledger_path, bets, 1000.0)
    print(f'final_bankroll={final:.2f}')
    "
      2. Assert final_bankroll = 1000 - 5 = 995 (first bet), then 995 - 15 = 980 (after second)
    Expected Result: final_bankroll = 980.00
    Failure Indicators: Bankroll doesn't decrease by total stake
    Evidence: .omo/evidence/task-10-ledger-sequential.txt

  Scenario: Ledger CSV has all required columns
    Tool: Bash
    Preconditions: Module importable, temp directory exists
    Steps:
      1. Run: python -c "
    import tempfile, csv
    from pathlib import Path
    from src.betting.ledger import init_ledger, LEDGER_COLUMNS
    tmp = Path(tempfile.mkdtemp())
    path = init_ledger(tmp / 'ledger.csv')
    with open(path) as f:
        reader = csv.DictReader(f)
        actual = reader.fieldnames
    print(f'expected_cols={len(LEDGER_COLUMNS)} actual_cols={len(actual)}')
    print(f'match={actual == LEDGER_COLUMNS}')
    "
      2. Assert expected_cols = actual_cols = 17
      3. Assert match=True
    Expected Result: Exactly 17 columns, names match LEDGER_COLUMNS
    Failure Indicators: Column count mismatch, name mismatch
    Evidence: .omo/evidence/task-10-ledger-schema.txt
  ```

  **Commit**: YES (groups with Tasks 11, 12 in Wave 3)
  - Message: `feat(betting): add paper bet ledger with append-only CSV`
  - Files: `src/betting/ledger.py`, `tests/betting/test_ledger.py`

- [x] 11. Betting CLI — full pipeline entry point

  **What to do**:
  - Create `src/betting/cli.py`:
    - `build_betting_parser()`: argparse with:
      - `--odds PATH` (required): Path to odds CSV file
      - `--bankroll FLOAT` (default 1000.0): Starting bankroll
      - `--no-fetch`: Skip live IMF/BIS data, use mock data
      - `--output-dir PATH` (default `./output/betting`): Output directory
      - `--min-ev FLOAT` (default 0.03): Minimum EV threshold (3% for paper betting; raise to 0.05 for Phase 2 live)
      - `--min-odds FLOAT` (default 1.50): Minimum decimal odds
      - `--max-odds FLOAT` (default 3.50): Maximum decimal odds
      - `--kelly-fraction FLOAT` (default 0.25): Kelly fraction
      - `--max-stake-pct FLOAT` (default 0.05): Max stake as fraction of bankroll
    - `main(argv) -> int`:
      1. Parse args
      2. Load dataset: import from `src.aggregate.build_dataset`, `src.aggregate.normalize_scores`
      3. Get upcoming matches: `src.schedule.get_upcoming_matches(cutoff_date)`
      4. Convert to ISO3, skip knockout placeholders
      5. Predict all matches: `src.predict.predict_all_upcoming(matches, dataset, seed=None)` ← NO SEED for betting
      6. Load odds: `CsvOddsProvider(args.odds).fetch_odds()`
      7. Validate odds: use `validate_odds_csv`
      8. Select bets: `select_bets(predictions, odds_data)`
      9. Apply Kelly sizing: `recommend_stake(bankroll, p_model, odds)` for each candidate
      10. Output ranked table to stdout (match, market, selection, odds, model_prob, edge, EV, stake, decision)
      11. Log to ledger: `log_bets(ledger_path, candidates, bankroll)`
      12. Summary: "N bets found | total stake: €X | remaining bankroll: €Y"
  - Create `tests/betting/test_cli.py`:
    - `test_help` — `python -m src.betting.cli --help` → exit 0
    - `test_missing_odds` — exits with error when --odds not provided
    - `test_e2e_with_mock` — full pipeline with mock data → exit 0, paper_bet_ledger.csv exists

  **Must NOT do**:
  - Do NOT use a seed for `predict_all_upcoming` — betting probabilities must be deterministic (no noise)
  - Do NOT modify `src/cli.py` — betting CLI is a separate entry point
  - Do NOT output the noisy score predictions — only betting recommendations

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integration task — orchestrates all betting modules, ~120 lines, multiple imports from existing and new modules
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential — needs everything)
  - **Blocks**: Task 12 (E2E test on CLI)
  - **Blocked By**: Tasks 1, 4, 8, 10 (needs clean xG, odds parser, EV selector, ledger)

  **References**:
  - `src/cli.py:79-127` — Existing CLI pattern: `build_parser()` and `main(argv)` function structure. Follow this exact style: argparse, `_valid_iso_date`, `DEFAULT_*` constants.
  - `src/cli.py:286-348` — `main()` function: pipeline orchestration pattern. Steps 1-8 in `main()` match closely.
  - `src/cli.py:148-181` — `_mock_data()`: Reuse this for `--no-fetch` mode.
  - `src/cli.py:239-258` — `_convert_match_to_iso3()`: Reuse for matching prediction teams to odds data.
  - `src/schedule.py:185-214` — `get_upcoming_matches()`: Returns list of matches filtered by cutoff date.
  - `src/betting/odds.py` (Task 4 output) — `CsvOddsProvider`, `validate_odds_csv`
  - `src/betting/selector.py` (Tasks 8, 9 output) — `select_bets`, `recommend_stake`
  - `src/betting/ledger.py` (Task 10 output) — `init_ledger`, `log_bets`
  - `src/betting/validation.py` (Task 5 output) — `resolve_team_name`

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Test file: `tests/betting/test_cli.py` created with 3 test functions
  - [ ] `python -m pytest tests/betting/test_cli.py -v` → PASS (3 tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: CLI runs end-to-end with mock data and sample odds
    Tool: Bash
    Preconditions: All betting modules built, tests/fixtures/sample_odds.csv exists
    Steps:
      1. Run: python -m src.betting.cli --odds tests/fixtures/sample_odds.csv --no-fetch --bankroll 1000 --output-dir /tmp/betting_e2e
      2. Assert exit code 0
      3. Assert stdout contains "bet" or "candidate" or "ledger" (not empty)
      4. Assert /tmp/betting_e2e/paper_bet_ledger.csv exists
      5. Read output and check for "Total" or "bankroll" summary line
    Expected Result: Exit 0, ledger file created, summary printed
    Failure Indicators: Non-zero exit, no ledger file, silent failure
    Evidence: .omo/evidence/task-11-cli-e2e.txt

  Scenario: CLI handles missing odds file gracefully
    Tool: Bash
    Preconditions: Module importable
    Steps:
      1. Run: python -m src.betting.cli --odds /nonexistent/path.csv --no-fetch 2>&1; echo "EXIT=$?"
      2. Assert EXIT != 0 (non-zero exit)
      3. Assert stderr/stdout contains error message about file not found
    Expected Result: Non-zero exit with clear "file not found" error
    Failure Indicators: Exit 0, vague error, crash/stack trace
    Evidence: .omo/evidence/task-11-cli-missing-file.txt
  ```

  **Commit**: YES (groups with Tasks 10, 12 in Wave 3)
  - Message: `feat(betting): add betting CLI pipeline entry point`
  - Files: `src/betting/cli.py`, `tests/betting/test_cli.py`

- [x] 12. End-to-end integration test + fixtures — full pipeline verification

  **What to do**:
  - Create `tests/fixtures/sample_odds.csv` with 5 realistic WC2026 group-stage odds:
    ```
    timestamp,event_id,kickoff,home,away,book,market,selection,line,decimal_odds
    2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Spain,,1.22
    2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Draw,,5.50
    2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Cabo Verde,,15.00
    2026-06-15T12:00:00,WC2026-14,2026-06-15T21:00:00,Belgium,Egypt,bet365,1X2,Belgium,,1.70
    2026-06-15T12:00:00,WC2026-14,2026-06-15T21:00:00,Belgium,Egypt,bet365,1X2,Draw,,3.60
    2026-06-15T12:00:00,WC2026-14,2026-06-15T21:00:00,Belgium,Egypt,bet365,1X2,Egypt,,5.00
    2026-06-15T12:00:00,WC2026-15,2026-06-15T15:00:00,Saudi Arabia,Uruguay,bet365,1X2,Saudi Arabia,,3.75
    2026-06-15T12:00:00,WC2026-15,2026-06-15T15:00:00,Saudi Arabia,Uruguay,bet365,1X2,Draw,,3.25
    2026-06-15T12:00:00,WC2026-15,2026-06-15T15:00:00,Saudi Arabia,Uruguay,bet365,1X2,Uruguay,,2.05
    2026-06-15T12:00:00,WC2026-16,2026-06-15T12:00:00,IR Iran,New Zealand,bet365,1X2,IR Iran,,1.90
    2026-06-15T12:00:00,WC2026-16,2026-06-15T12:00:00,IR Iran,New Zealand,bet365,1X2,Draw,,3.20
    2026-06-15T12:00:00,WC2026-16,2026-06-15T12:00:00,IR Iran,New Zealand,bet365,1X2,New Zealand,,4.50
    2026-06-15T12:00:00,WC2026-17,2026-06-16T21:00:00,France,Senegal,bet365,1X2,France,,1.55
    2026-06-15T12:00:00,WC2026-17,2026-06-16T21:00:00,France,Senegal,bet365,1X2,Draw,,3.80
    2026-06-15T12:00:00,WC2026-17,2026-06-16T21:00:00,France,Senegal,bet365,1X2,Senegal,,6.50
    ```
  - Create `tests/fixtures/sample_odds_invalid.csv` with deliberate errors:
    - Missing "home" column
    - Negative odds value (-1.5)
    - Unknown team name ("Mars")
  - Add `tests/betting/test_cli.py::test_e2e_pipeline` integration test:
    - Runs full CLI with `--no-fetch --odds tests/fixtures/sample_odds.csv --bankroll 1000`
    - Verifies exit code 0
    - Verifies ledger CSV exists with header + ≥1 data row
    - Verifies stdout contains expected fields (model_prob, ev, stake)
  - Verify regression gate:
    - `python -m pytest tests/ -v --ignore=tests/betting/` → all existing tests pass
    - `python -m src.cli --seed 42 --no-fetch --output-dir /tmp/regression_test` → exit 0

  **Must NOT do**:
  - Do NOT modify any existing test file outside `tests/betting/`
  - Do NOT skip any existing test — all must pass

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: CSV fixture files + one integration test, ~50 lines
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential — needs Task 11 CLI working)
  - **Blocks**: None (last implementation task before Final Verification)
  - **Blocked By**: Task 11 (needs CLI working)

  **References**:
  - `tests/conftest.py` — Existing test fixtures pattern. Use for any shared betting test fixtures.
  - `tests/test_cli.py` — Existing CLI integration test pattern. Follow subprocess or direct `main()` call style.
  - `src/schedule.py:28-104` — Team names to use in fixtures: "Spain", "Cabo Verde", "Belgium", "Egypt", "Saudi Arabia", "Uruguay", "IR Iran", "New Zealand", "France", "Senegal"

  **Acceptance Criteria**:

  **If TDD (tests enabled):**
  - [ ] Fixture files created: `tests/fixtures/sample_odds.csv`, `tests/fixtures/sample_odds_invalid.csv`
  - [ ] E2E test added to `tests/betting/test_cli.py`
  - [ ] `python -m pytest tests/ -v` → ALL tests pass (existing + new)
  - [ ] `python -m pytest tests/ -v --ignore=tests/betting/` → ALL existing tests pass (regression gate)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Full pipeline produces valid ledger CSV with bet candidates
    Tool: Bash
    Preconditions: All modules built, fixtures exist
    Steps:
      1. Run: python -m src.betting.cli --odds tests/fixtures/sample_odds.csv --no-fetch --bankroll 1000 --output-dir /tmp/betting_final 2>&1 | tee /tmp/betting_output.txt
      2. Run: python -c "
    import csv
    with open('/tmp/betting_final/paper_bet_ledger.csv') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f'rows={len(rows)}, cols={len(rows[0]) if rows else 0}')
    for r in rows:
        print(f'  {r[\"team_a\"]} vs {r[\"team_b\"]}: {r[\"selection\"]} @ {r[\"decimal_odds\"]} EV={r[\"ev\"]} stake={r[\"stake\"]}')
    "
      3. Assert rows > 0 (at least one bet candidate)
      4. Assert each row has non-empty ev, stake, selection fields
    Expected Result: ≥1 bet candidates logged with valid EV and stake
    Failure Indicators: Empty ledger, malformed rows, missing columns
    Evidence: .omo/evidence/task-12-e2e-pipeline.txt

  Scenario: Regression — existing predictor CLI still works unchanged
    Tool: Bash
    Preconditions: src/predict.py modified (Task 1)
    Steps:
      1. Run: python -m src.cli --seed 42 --no-fetch --output-dir /tmp/regression_test 2>&1
      2. Assert exit code 0
      3. Assert /tmp/regression_test/predictions.csv exists
      4. Run: python -m pytest tests/ -v --ignore=tests/betting/ 2>&1 | tail -5
      5. Assert output contains "passed" and not "failed"
    Expected Result: Existing CLI works identically, all existing tests pass
    Failure Indicators: Non-zero exit, missing CSV, test failures
    Evidence: .omo/evidence/task-12-regression-gate.txt
  ```

  **Commit**: YES (groups with Tasks 10, 11 in Wave 3)
  - Message: `feat(betting): add E2E integration test and odds CSV fixtures`
  - Files: `tests/fixtures/sample_odds.csv`, `tests/fixtures/sample_odds_invalid.csv`, `tests/betting/test_cli.py`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**
> **Never mark F1-F4 as checked before getting user's okay.** Rejection or user feedback → fix → re-run → present again → wait for okay.

- [x] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found.
  - Clean xG in `predict_match()` return dict? → Read `src/predict.py`, grep for `team_a_clean_xg`
  - No scipy import? → `grep -r "import scipy" src/betting/`
  - No modification of `formula.py`, `aggregate.py`, `schedule.py`, `fifa_data.py`, `country_map.py`? → Check git diff
  - No Dixon-Coles? → `grep -r "dixon" src/betting/`
  - No web/API code? → Check no Flask/FastAPI imports
  - Regression: existing CLI still works? → Run `python -m src.cli --seed 42 --no-fetch`
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [x] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v`. Review all new files for:
  - `as any`, `@ts-ignore`, bare `except:`
  - `console.log`-style debug prints left in
  - Commented-out code blocks
  - Unused imports (check: no `import scipy`)
  - Magic numbers without explanation
  - Functions > 50 lines without justification
  - Missing docstrings on public functions
  - AI slop: excessive comments, over-abstraction, generic names (`data`, `result`, `item`, `temp`)
  Output: `Tests [N pass/N fail] | Files [N clean/N issues] | Slop [CLEAN/N items] | VERDICT`

- [x] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence.
  - Task 1: Clean xG extraction → verify clean ≠ noisy
  - Task 2: Poisson PMF → golden values match
  - Task 3: 1X2 balanced match → symmetry holds
  - Task 4: CSV parsing → valid and invalid cases
  - Task 5: Team name resolution → all 48 teams resolve
  - Task 6: Totals + BTTS → edge cases
  - Task 7: Overround removal → sum = 1.0
  - Task 8: EV filter → positive passes, negative excluded
  - Task 9: Kelly cap → 5% hard cap enforced
  - Task 10: Ledger → sequential bankroll updates
  - Task 11: CLI → e2e run, missing file error
  - Task 12: Full pipeline → regression gate
  Save to `.omo/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Evidence [N files] | Regression [PASS/FAIL] | VERDICT`

- [x] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (`git diff main...HEAD` or `git log --oneline`). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance.
  - Every new module in `src/betting/` matches a planned task
  - Every planned file exists and is non-empty
  - No unplanned files in `src/` outside `src/betting/`
  - No unplanned dependencies in `pyproject.toml`
  - All 17 ledger columns match spec
  - Regression gate: `git diff --stat` shows only planned files modified
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **1, 2, 4, 5** (Wave 1): `feat(betting): add clean xG, Poisson engine, validation, and odds parser` — `src/predict.py`, `src/betting/__init__.py`, `src/betting/probabilities.py`, `src/betting/odds.py`, `src/betting/validation.py`, `tests/betting/*`, `tests/fixtures/*`
  - Pre-commit: `python -m pytest tests/ -v --ignore=tests/betting/`
- **3, 6, 7** (Wave 2a): `feat(betting): add 1X2, totals, BTTS calculators and overround removal` — `src/betting/probabilities.py`, `src/betting/odds.py`, `tests/betting/*`
  - Pre-commit: `python -m pytest tests/ -v`
- **8, 9** (Wave 2b): `feat(betting): add EV calculator and Kelly staking engine` — `src/betting/selector.py`, `tests/betting/*`
  - Pre-commit: `python -m pytest tests/ -v`
- **10, 11, 12** (Wave 3): `feat(betting): add paper bet ledger, CLI, and E2E integration tests` — `src/betting/ledger.py`, `src/betting/cli.py`, `tests/betting/*`
  - Pre-commit: `python -m pytest tests/ -v`

---

## Success Criteria

### Verification Commands
```bash
# Regression gate — existing tests must still pass
python -m pytest tests/ -v --ignore=tests/betting/
# Expected: ALL existing tests pass (currently ~50+ test functions)

# Full test suite with betting modules
python -m pytest tests/ -v
# Expected: ALL tests pass, 0 failures, 0 errors

# Existing CLI still works
python -m src.cli --seed 42 --no-fetch --output-dir /tmp/test_existing
# Expected: exit 0, predictions.csv exists

# Betting CLI works with mock data and sample odds
python -m src.betting.cli --odds tests/fixtures/sample_odds.csv --no-fetch --bankroll 1000 --output-dir /tmp/betting_test
# Expected: exit 0, paper_bet_ledger.csv exists with N rows
```

### Final Checklist
- [x] All "Must Have" present (clean xG, Poisson 1X2, odds parser, EV, Kelly, ledger, CLI)
- [x] All "Must NOT Have" absent (no scipy, no scraping, no Dixon-Coles, no DNB, no dashboard)
- [x] All existing tests pass (`python -m pytest tests/ -v --ignore=tests/betting/`)
- [x] All new betting tests pass
- [x] Existing CLI `python -m src.cli --seed 42 --no-fetch` works unchanged
- [x] Betting CLI produces valid ledger CSV with correct schema
