# World Cup 2026 Prediction Script — Bond Vigilantes Model

## TL;DR

> **Quick Summary**: Build a Python script that applies the Bond Vigilantes 50/50 economic-FIFA prediction model to all remaining World Cup 2026 group stage matches, fetching live economic data via IMF/BIS APIs and outputting CSV + Excel prediction theses.
>
> **Deliverables**:
> - `src/` — 10 Python modules (formula, fetchers, aggregation, prediction, cli, output)
> - `tests/` — 10 corresponding pytest test files (TDD)
> - `world_cup_predictions.csv` — parseable match predictions
> - `world_cup_predictions.xlsx` — formatted spreadsheet thesis
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES — 5 waves (12 implementation + 4 final review tasks)
> **Critical Path**: Task 2 → Task 6/7 → Task 9 → Task 10 → Task 11/12

---

## Context

### Original Request
Create a Python script to replicate the Bond Vigilantes World Cup 2026 investment thesis model, apply it to all upcoming tournament matches, and output predictions in CSV/Excel parseable format.

### Interview Summary
**Key Discussions**:
- Python + TDD with pytest: Confirmed by user
- Live API data fetch: IMF WEO DataMapper API v1 (GDP, inflation, unemployment, debt/GDP, population), BIS SDMX API (policy rates), FIFA rankings hardcoded from April 1, 2026
- Output: Both CSV + Excel (.xlsx) with match predictions plus intermediate calculations
- Scope: Remaining group stage matches only (match #9 onwards, skipping already-played #1-4 and today's #5-8). Knockout excluded (pairings depend on group results)
- Model inferences confirmed: Min-max normalization, xG = blended_score × 4, Gaussian noise σ=0.3, no home advantage

**Research Findings**:
- Complete FIFA April 1, 2026 rankings for all 48 teams (France #1 at 1877.32 pts → New Zealand #85 at 1281.57 pts)
- 104-match schedule: 72 group stage (Jun 11-27) + 32 knockout (Jun 28 - Jul 19)
- Already played: matches #1-4 (Jun 11-12), today's #5-8 (Jun 13). Target: matches #9-72
- IMF DataMapper API v1: free, no auth, base URL `https://www.imf.org/external/datamapper/api/v1/`
- BIS SDMX API: free, no auth, flow `WS_CBPOL` with key `M.{ISO3}`
- Recommended Python stack: `wbgapi` (World Bank fallback), `requests`, `pandas`, `openpyxl`, `pytest`

### Metis Review
**Identified Gaps** (addressed):
- `(LOG10(Pop)-6)^1.2` undefined for Pop < 1M: Resolved with `max(LOG10(Pop)-6, 0)^1.2` clamp (small nations get 0 population factor)
- Unit conventions mixed: Documented explicitly — GDP/Infl/Rate as percentages, Unemp as decimal, Debt/GDP as ratio
- Score → match prediction pipeline: Defined as `xG = blended_score × 4 + N(0, 0.3)`, integer via `round()`
- BIS coverage gaps (~20 nations): Fallback to IMF WEO interest rate or World Bank data
- Country name mapping: Comprehensive 48-nation lookup table bridging FIFA → ISO3 → IMF → World Bank
- Reproducibility: `--seed` flag (default: 42), `--cutoff-date` parameter

---

## Work Objectives

### Core Objective
Build a reproducible Python script that applies the Bond Vigilantes 50/50 economic-FIFA model to predict all remaining World Cup 2026 group stage matches and exports the results as a CSV + Excel investment thesis.

### Concrete Deliverables
- `src/formula.py` — Economic model formula engine
- `src/fifa_data.py` — FIFA April 2026 ranking data (48 nations)
- `src/country_map.py` — Country name mapping table (FIFA ↔ ISO3 ↔ IMF ↔ WB)
- `src/schedule.py` — World Cup 2026 match schedule data
- `src/imf_fetcher.py` — IMF WEO DataMapper API client
- `src/bis_fetcher.py` — BIS policy rate API client
- `src/validation.py` — Data validation schema and checks
- `src/aggregate.py` — Merge all data sources into unified dataset
- `src/predict.py` — Normalization, blending, xG calculation, match prediction engine
- `src/cli.py` — CLI interface (--seed, --cutoff-date, --output-dir)
- `src/output.py` — CSV + Excel output generator
- `tests/` — 10 corresponding pytest test files

### Definition of Done
- [ ] `python -m pytest tests/` → ALL tests pass (0 failures)
- [ ] `python -m src.cli --cutoff-date 2026-06-13 --output-dir ./output` runs to completion in <60s
- [ ] `output/world_cup_predictions.csv` is valid CSV with N match rows
- [ ] `output/world_cup_predictions.xlsx` is valid Excel workbook
- [ ] Predictions only include matches #9-72 (no already-played or knockout matches)
- [ ] Script produces identical output on repeated runs with same `--seed`

### Must Have
- Exact Bond Vigilantes formula implementation with correct unit conventions
- `(LOG10(Pop)-6)^1.2` clamped at 0 for Pop < 1M populations (Curacao, etc.)
- 48-country name mapping table bridging all 3 data source naming schemes
- `--seed` flag for deterministic reproducibility (default: 42)
- `--cutoff-date` parameter (default: script execution date)
- Fallback strategy for missing BIS/IMF data
- TDD with pytest — ALL tests written before implementation
- CSV output with columns: match_number, group, date, team_a, team_b, predicted_score, team_a_xg, team_b_xg, team_a_econ_score, team_b_econ_score, team_a_fifa_score, team_b_fifa_score, team_a_blended, team_b_blended
- Excel output with same data + formatted spreadsheet

### Must NOT Have (Guardrails)
- **NO Monte Carlo simulation engine** — single-pass calculation with Gaussian noise only
- **NO knockout match predictions** — pairings depend on group results (unknowable)
- **NO already-played matches** — matches #1-4 excluded, #5-8 excluded (today's matches)
- **NO web scraping** — BeautifulSoup/Selenium forbidden. APIs only. Missing data → fallback file or warning
- **NO visualizations** — no matplotlib, plotly, charts. CSV + Excel only
- **NO configurable model weights** — hardcode 50/50 blend, σ=0.3 noise
- **NO `pandas-datareader`** — abandoned library with broken readers
- **NO home advantage factor** — neutral venue model per thesis

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** - ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (empty workspace — pytest must be set up)
- **Automated tests**: TDD — each task writes tests FIRST, then implementation
- **Framework**: pytest (to be installed in Task 1)
- **TDD workflow**: RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.omo/evidence/task-{N}-{scenario-slug}.{ext}`.

- **API/Backend**: Use Bash (curl + python) — verify API responses, data shapes, outputs
- **Library/Module**: Use Bash (python -c) — import, call functions, compare output
- **CLI**: Use interactive_bash (tmux) — run script, pass flags, validate output files

---

## Execution Strategy

### Parallel Execution Waves

> This is a pipeline project with inherent sequential dependencies (fetch → aggregate → predict → output).
> Waves 1-2 maximize parallelism; Waves 3-4 are unavoidable single-task bottlenecks.

```
Wave 1 (Start Immediately — 5 parallel foundation tasks):
├── Task 1: Project scaffolding + pytest setup [quick]
├── Task 2: Country mapping table (48 nations × 3 schemes) [quick]
├── Task 3: Match schedule data module [quick]
├── Task 4: FIFA ranking data module [quick]
└── Task 5: Economic formula engine [quick]

Wave 2 (After Wave 1 — 3 parallel data pipeline tasks):
├── Task 6: IMF WEO data fetcher [unspecified-high]
├── Task 7: BIS policy rate fetcher [unspecified-high]
└── Task 8: Data validation schema + module [quick]

Wave 3 (After Wave 2 — bottleneck: aggregation pipeline):
└── Task 9: Data aggregation + normalization [unspecified-high]

Wave 4 (After Wave 3 — bottleneck: prediction engine):
└── Task 10: Prediction engine (blending, xG, noise, match results) [unspecified-high]

Wave 5 (After Wave 4 — 2 parallel output tasks):
├── Task 11: CLI + main entry point [quick]
└── Task 12: CSV + Excel output generator [unspecified-high]

Critical Path: Task 2 → Task 6/7 → Task 9 → Task 10 → Task 11/12
Parallel Speedup: ~40% faster than sequential (5→3→1→1→2 vs 12 sequential)
Max Concurrent: 5 (Wave 1)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | - | 2, 5, 6, 7, 8, 11 | 1 |
| 2 | - | 5, 6, 7, 8, 9 | 1 |
| 3 | - | 10, 12 | 1 |
| 4 | - | 9, 10 | 1 |
| 5 | 2 (test data) | 9, 10 | 1 |
| 6 | 2 (ISO3 codes) | 9 | 2 |
| 7 | 2 (ISO3 codes) | 9 | 2 |
| 8 | 2 (country list) | 9 | 2 |
| 9 | 4, 5, 6, 7, 8 | 10 | 3 |
| 10 | 3, 4, 9 | 11, 12 | 4 |
| 11 | 10 | - | 5 |
| 12 | 3, 10 | - | 5 |

### Agent Dispatch Summary

- **Wave 1**: **5** — T1-T4 → `quick`, T5 → `quick`
- **Wave 2**: **3** — T6 → `unspecified-high`, T7 → `unspecified-high`, T8 → `quick`
- **Wave 3**: **1** — T9 → `unspecified-high`
- **Wave 4**: **1** — T10 → `unspecified-high`
- **Wave 5**: **2** — T11 → `quick`, T12 → `unspecified-high`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. Project Scaffolding + Pytest Setup

  **What to do**:
  - Create `pyproject.toml` with project metadata, Python 3.11+ requirement
  - Define dependencies: `pandas`, `openpyxl`, `requests`, `wbgapi`
  - Define dev dependencies: `pytest`, `pytest-mock`, `pytest-cov`
  - Create `src/__init__.py` and `tests/__init__.py`
  - Create `tests/conftest.py` with shared fixtures (sample country list, mock API responses)
  - Write `tests/test_scaffolding.py`: verify imports work, verify pytest runs, verify Python version ≥ 3.11
  - Create `.gitignore` (exclude `__pycache__`, `.pytest_cache`, `output/`)
  - Create `README.md` with setup instructions (`pip install -e .`, `pytest`)

  **Must NOT do**:
  - Do NOT add visualization libraries (matplotlib, plotly, seaborn)
  - Do NOT add web frameworks (flask, fastapi, django)
  - Do NOT add linters/formatters beyond what pytest needs (black/ruff optional but not required)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard project scaffolding — no domain knowledge needed, just file creation and package setup
  - **Skills**: None
  - **Skills Evaluated but Omitted**:
    - `git-master`: Not needed — repo isn't git-initialized and we're not committing yet

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5)
  - **Blocks**: Tasks 6, 7, 8, 11 (these import from src/)
  - **Blocked By**: None (can start immediately)

  **References**:
  - **Pattern References**: N/A (greenfield project — no existing Python code in workspace)
  - **External References**:
    - `pyproject.toml` standard: PEP 621 — `[project]` table with `dependencies` and `[project.optional-dependencies]`
    - pytest docs: `https://docs.pytest.org/en/stable/getting-started.html` — basic test structure, conftest.py fixtures

  **Acceptance Criteria**:
  - [ ] `pip install -e .` succeeds without errors
  - [ ] `python -c "import pandas; import openpyxl; import requests; print('OK')"` prints "OK"
  - [ ] `python -m pytest tests/test_scaffolding.py -v` → PASS (1+ tests, 0 failures)
  - [ ] `python --version` → Python 3.11 or higher

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — project installs and imports work
    Tool: Bash
    Preconditions: pyproject.toml exists, virtual env activated
    Steps:
      1. pip install -e . 2>&1 | tail -5
      2. python -c "import pandas; import openpyxl; import requests; print('ALL_IMPORTS_OK')"
      3. python -m pytest tests/test_scaffolding.py -v 2>&1
    Expected Result: ALL_IMPORTS_OK printed; pytest output shows "1 passed"
    Failure Indicators: ImportError, ModuleNotFoundError, pytest shows failures
    Evidence: .omo/evidence/task-1-scaffolding-imports.txt

  Scenario: Edge case — pytest fails gracefully on missing test
    Tool: Bash
    Preconditions: tests/ exists but is empty
    Steps:
      1. python -m pytest tests/ --collect-only 2>&1
    Expected Result: "no tests collected" or similar — no crash
    Evidence: .omo/evidence/task-1-pytest-empty.txt
  ```

  **Commit**: YES (groups with Task 2-5 in Wave 1)
  - Message: `chore: initialize project scaffolding with pytest`
  - Files: `pyproject.toml`, `src/__init__.py`, `tests/__init__.py`, `tests/conftest.py`, `tests/test_scaffolding.py`, `.gitignore`, `README.md`

- [ ] 2. Country Mapping Table (48 Nations × 3 Naming Schemes)

  **What to do**:
  - Create `src/country_map.py` with a `COUNTRY_MAP` dict (48 entries)
  - Each entry keys: `fifa_name`, `iso3`, `imf_code` (ISO3 same as iso3 for IMF), `wb_code` (ISO3 for World Bank)
  - Include all 48 World Cup 2026 nations with their groups (A-L)
  - Provide lookup functions: `get_iso3(fifa_name)`, `get_fifa_name(iso3)`, `get_group(iso3)`
  - Write `tests/test_country_map.py` FIRST (TDD):
    - Test: 48 entries exist
    - Test: every ISO3 is 3 uppercase letters
    - Test: bidirectional lookup works (fifa_name → iso3 → fifa_name roundtrip)
    - Test: all 12 groups (A-L) are represented
    - Test: specific tricky mappings: "Korea Republic" → "KOR", "Côte d'Ivoire" → "CIV", "IR Iran" → "IRN", "USA" → "USA", "Türkiye" → "TUR"

  **Must NOT do**:
  - Do NOT include teams not in World Cup 2026 (Italy, Denmark, Nigeria, etc.)
  - Do NOT hardcode FIFA ranking points here (that's Task 4)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure data structure — 48-entry dict with simple lookup functions, no external dependencies
  - **Skills**: None
  - **Skills Evaluated but Omitted**:
    - `librarian`: Not needed — all 48 teams confirmed from research (groups, ISO3 codes verified)

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5)
  - **Blocks**: Tasks 5, 6, 7, 8, 9
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL):

  **Pattern References**: N/A — greenfield data module

  **Data References** (from research — use these exact values):
  - World Cup groups confirmed by librarian research:
    Group A: Mexico, South Africa, Korea Republic, Czechia
    Group B: Canada, Bosnia and Herzegovina, Qatar, Switzerland
    Group C: Brazil, Morocco, Haiti, Scotland
    Group D: USA, Paraguay, Australia, Türkiye
    Group E: Germany, Curaçao, Côte d'Ivoire, Ecuador
    Group F: Netherlands, Japan, Sweden, Tunisia
    Group G: Belgium, Egypt, IR Iran, New Zealand
    Group H: Spain, Cabo Verde, Saudi Arabia, Uruguay
    Group I: France, Senegal, Iraq, Norway
    Group J: Argentina, Algeria, Austria, Jordan
    Group K: Portugal, DR Congo, Uzbekistan, Colombia
    Group L: England, Croatia, Ghana, Panama
  - ISO3 codes: MEX, ZAF, KOR, CZE, CAN, BIH, QAT, CHE, BRA, MAR, HTI, SCO, USA, PRY, AUS, TUR, DEU, CUW, CIV, ECU, NLD, JPN, SWE, TUN, BEL, EGY, IRN, NZL, ESP, CPV, SAU, URY, FRA, SEN, IRQ, NOR, ARG, DZA, AUT, JOR, PRT, COD, UZB, COL, GBR, HRV, GHA, PAN

  **WHY Each Reference Matters**:
  - Group assignments determine match pairings (used by Task 3 and Task 12)
  - ISO3 codes are the bridge between FIFA names and API calls (IMF, BIS, World Bank all use ISO3)
  - Correct codes are critical — wrong ISO3 = failed API calls across Tasks 6, 7, 9

  **Acceptance Criteria**:
  - [ ] File created: `src/country_map.py`
  - [ ] `python -m pytest tests/test_country_map.py -v` → PASS (5+ tests, 0 failures)
  - [ ] `python -c "from src.country_map import COUNTRY_MAP; assert len(COUNTRY_MAP) == 48"` succeeds

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — all 48 nations resolve correctly
    Tool: Bash
    Preconditions: src/country_map.py exists
    Steps:
      1. python -c "
      from src.country_map import COUNTRY_MAP, get_iso3
      print(f'Total nations: {len(COUNTRY_MAP)}')
      print(get_iso3('USA'))
      print(get_iso3('Korea Republic'))
      print(get_iso3('Côte d\'Ivoire'))
      print(get_iso3('Curaçao'))
      "
    Expected Result: Prints "Total nations: 48", then "USA", "KOR", "CIV", "CUW"
    Failure Indicators: KeyError, count ≠ 48, wrong ISO3 code
    Evidence: .omo/evidence/task-2-country-resolve.txt

  Scenario: Error case — unknown country raises KeyError
    Tool: Bash
    Preconditions: src/country_map.py exists
    Steps:
      1. python -c "
      from src.country_map import get_iso3
      try:
          get_iso3('Italy')
          print('FAIL: should have raised')
      except KeyError as e:
          print(f'OK: KeyError raised: {e}')
      "
    Expected Result: "OK: KeyError raised: ..." (Italy not in World Cup)
    Failure Indicators: No exception raised, or wrong exception type
    Evidence: .omo/evidence/task-2-keyerror.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat: add 48-nation country mapping table with ISO3 codes`
  - Files: `src/country_map.py`, `tests/test_country_map.py`

- [ ] 3. Match Schedule Data Module

  **What to do**:
  - Create `src/schedule.py` with complete World Cup 2026 group stage schedule
  - Data structure: list of dicts with keys: `match_number` (int), `group` (str A-L), `date` (ISO date string), `team_a` (FIFA name), `team_b` (FIFA name), `matchday` (int 1-3), `status` (str: "played", "today", "upcoming")
  - Include all 72 group stage matches (#1-72) with correct dates and pairings
  - Include knockout matches (#73-104) with `status: "knockout"` for structural awareness
  - Provide `get_upcoming_matches(cutoff_date)` function — returns only "upcoming" matches on/before cutoff
  - Provide `get_group_matches(group)` — returns all matches for a given group
  - Write `tests/test_schedule.py` FIRST (TDD):
    - Test: total 104 matches (72 group + 32 knockout)
    - Test: 12 groups each have exactly 6 matches
    - Test: `get_upcoming_matches("2026-06-13")` excludes matches #1-8
    - Test: `get_upcoming_matches("2026-06-14")` returns only matches #9+ that haven't started yet
    - Test: match #36 is Tunisia vs Japan (the 1,000th World Cup match — verify correctness)
    - Test: every match has valid team names (all in COUNTRY_MAP from Task 2)

  **Must NOT do**:
  - Do NOT include scores/results for already-played matches (we only predict, don't track results)
  - Do NOT include knockout bracket pairings as resolved (they depend on group results — mark as `status: "knockout"`)
  - Do NOT use external APIs for the schedule — hardcode from confirmed research

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure data structure — schedule is deterministic, already confirmed from research
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5)
  - **Blocks**: Tasks 10, 12 (need schedule to filter upcoming matches)
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL):

  **Data References** (from librarian research — use these exact values):
  - Match #1: Jun 11, Mexico vs South Africa, Group A, MD1 → status: "played"
  - Match #2: Jun 11, Korea Republic vs Czechia, Group A, MD1 → status: "played"
  - Match #3: Jun 12, Canada vs Bosnia and Herzegovina, Group B, MD1 → status: "played"
  - Match #4: Jun 12, USA vs Paraguay, Group D, MD1 → status: "played"
  - Match #5: Jun 13, Qatar vs Switzerland, Group B, MD1 → status: "today"
  - Match #6: Jun 13, Brazil vs Morocco, Group C, MD1 → status: "today"
  - Match #7: Jun 13, Haiti vs Scotland, Group C, MD1 → status: "today"
  - Match #8: Jun 13, Australia vs Türkiye, Group D, MD1 → status: "today"
  - Matches #9-72: MD1 (Jun 14-17), MD2 (Jun 18-23), MD3 (Jun 24-27) → status: "upcoming"
  - Matches #73-104: Knockout (Jun 28 - Jul 19) → status: "knockout"
  - GROUP STAGE ONLY: 48 teams, 12 groups, 6 matches per group, 2 matches per MD per group

  Full schedule data confirmed by librarian research. Every match number, date, pairing verified against FIFA official schedule.

  **WHY Each Reference Matters**:
  - Match dates determine "upcoming" filter via cutoff_date
  - Team names must match COUNTRY_MAP keys exactly (Task 2 dependency)
  - Match numbers serve as unique identifiers in output CSV/Excel

  **Acceptance Criteria**:
  - [ ] File created: `src/schedule.py`
  - [ ] `python -m pytest tests/test_schedule.py -v` → PASS (6+ tests, 0 failures)
  - [ ] `python -c "from src.schedule import get_upcoming_matches; matches = get_upcoming_matches('2026-06-13'); print(len(matches))"` → prints number >= 64

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — upcoming matches filter works correctly
    Tool: Bash
    Preconditions: src/schedule.py exists
    Steps:
      1. python -c "
      from src.schedule import get_upcoming_matches
      upcoming = get_upcoming_matches('2026-06-13')
      print(f'Upcoming matches: {len(upcoming)}')
      for m in upcoming[:3]:
          print(f'{m[\"match_number\"]}: {m[\"team_a\"]} vs {m[\"team_b\"]} ({m[\"date\"]})')
      # Verify no match numbers 1-8
      played = [m['match_number'] for m in upcoming if m['match_number'] <= 8]
      print(f'Played/today matches in upcoming: {played}')
      "
    Expected Result: Upcoming count ≥ 64; first 3 are matches #9-11; "Played/today matches in upcoming: []"
    Failure Indicators: Matches #1-8 appear in upcoming list
    Evidence: .omo/evidence/task-3-upcoming-filter.txt

  Scenario: Edge case — different cutoff dates
    Tool: Bash
    Preconditions: src/schedule.py exists
    Steps:
      1. python -c "
      from src.schedule import get_upcoming_matches
      d14 = len(get_upcoming_matches('2026-06-14'))
      d18 = len(get_upcoming_matches('2026-06-18'))
      d25 = len(get_upcoming_matches('2026-06-25'))
      print(f'Jun 14: {d14}, Jun 18: {d18}, Jun 25: {d25}')
      print('MONOTONIC_DECREASE' if d14 >= d18 >= d25 else 'ERROR: not monotonic')
      "
    Expected Result: Counts decrease as cutoff advances; "MONOTONIC_DECREASE" printed
    Failure Indicators: Count increases, or "ERROR" printed
    Evidence: .omo/evidence/task-3-cutoff-dates.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat: add World Cup 2026 group stage schedule data`
  - Files: `src/schedule.py`, `tests/test_schedule.py`

- [ ] 4. FIFA Ranking Data Module

  **What to do**:
  - Create `src/fifa_data.py` with hardcoded FIFA April 1, 2026 ranking data for all 48 WC nations
  - Data structure: dict keyed by ISO3 with value = FIFA ranking points (float)
  - Include rank number for reference but model uses points, not rank
  - Write `tests/test_fifa_data.py` FIRST (TDD):
    - Test: 48 nations have FIFA ranking data
    - Test: France (#1) has 1877.32 points (within 0.01 tolerance)
    - Test: New Zealand (#85) has 1281.57 points (within 0.01 tolerance)
    - Test: points are monotonically decreasing (higher rank = lower points, except ties)
    - Test: all ISO3 codes exist in COUNTRY_MAP (cross-reference Task 2)
    - Test: all points are positive floats > 1000

  **Must NOT do**:
  - Do NOT fetch FIFA rankings from an API or website (hardcoded from confirmed April 1, 2026 data)
  - Do NOT include nations not in World Cup 2026 (Italy, Denmark, Nigeria — they didn't qualify)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure data module — hardcoded values from confirmed research, no external dependencies
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5)
  - **Blocks**: Tasks 9, 10 (need FIFA scores for normalization and prediction)
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL):

  **Data References** (from librarian research — April 1, 2026 official FIFA ranking):
  Use these exact values. All 48 teams confirmed:
  | ISO3 | FIFA Name | Points | Rank |
  |------|-----------|--------|------|
  | FRA | France | 1877.32 | 1 |
  | ESP | Spain | 1876.40 | 2 |
  | ARG | Argentina | 1874.81 | 3 |
  | GBR | England | 1825.97 | 4 |
  | PRT | Portugal | 1763.83 | 5 |
  | BRA | Brazil | 1761.16 | 6 |
  | NLD | Netherlands | 1757.87 | 7 |
  | MAR | Morocco | 1755.87 | 8 |
  | BEL | Belgium | 1734.71 | 9 |
  | DEU | Germany | 1730.37 | 10 |
  | HRV | Croatia | 1717.07 | 11 |
  | COL | Colombia | 1693.09 | 13 |
  | SEN | Senegal | 1688.99 | 14 |
  | MEX | Mexico | 1681.03 | 15 |
  | USA | USA | 1673.13 | 16 |
  | URY | Uruguay | 1673.07 | 17 |
  | JPN | Japan | 1660.43 | 18 |
  | CHE | Switzerland | 1649.40 | 19 |
  | IRN | IR Iran | 1615.30 | 21 |
  | TUR | Türkiye | 1599.04 | 22 |
  | ECU | Ecuador | 1594.78 | 23 |
  | AUT | Austria | 1593.45 | 24 |
  | KOR | Korea Republic | 1588.66 | 25 |
  | AUS | Australia | 1580.67 | 27 |
  | DZA | Algeria | 1564.26 | 28 |
  | EGY | Egypt | 1563.24 | 29 |
  | CAN | Canada | 1556.48 | 30 |
  | NOR | Norway | 1550.94 | 31 |
  | PAN | Panama | 1540.64 | 33 |
  | CIV | Côte d'Ivoire | 1532.98 | 34 |
  | SWE | Sweden | 1514.77 | 38 |
  | PRY | Paraguay | 1503.50 | 40 |
  | CZE | Czechia | 1501.38 | 41 |
  | SCO | Scotland | 1498.35 | 43 |
  | TUN | Tunisia | 1479.04 | 44 |
  | COD | DR Congo | 1478.35 | 46 |
  | UZB | Uzbekistan | 1465.34 | 50 |
  | QAT | Qatar | 1454.96 | 55 |
  | IRQ | Iraq | 1447.14 | 57 |
  | ZAF | South Africa | 1429.73 | 60 |
  | SAU | Saudi Arabia | 1421.43 | 61 |
  | JOR | Jordan | 1391.45 | 63 |
  | BIH | Bosnia and Herzegovina | 1385.84 | 65 |
  | CPV | Cabo Verde | 1366.13 | 69 |
  | GHA | Ghana | 1346.31 | 74 |
  | CUW | Curaçao | 1294.65 | 82 |
  | HTI | Haiti | 1291.71 | 83 |
  | NZL | New Zealand | 1281.57 | 85 |

  **WHY**: Exact official FIFA ranking points from April 1, 2026 — the date the Bond Vigilantes model specifies. Feed directly into the 50/50 blend.

  **Acceptance Criteria**:
  - [ ] File created: `src/fifa_data.py`
  - [ ] `python -m pytest tests/test_fifa_data.py -v` → PASS (5+ tests, 0 failures)
  - [ ] `python -c "from src.fifa_data import FIFA_DATA; assert len(FIFA_DATA) == 48; print(FIFA_DATA['FRA'])"` → 1877.32

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — all 48 nations have valid FIFA points
    Tool: Bash
    Preconditions: src/fifa_data.py exists
    Steps:
      1. python -c "
      from src.fifa_data import FIFA_DATA
      print(f'Total: {len(FIFA_DATA)}')
      print(f'France: {FIFA_DATA[\"FRA\"]}')
      print(f'New Zealand: {FIFA_DATA[\"NZL\"]}')
      print(f'Range: {max(FIFA_DATA.values()) - min(FIFA_DATA.values()):.2f}')
      all_positive = all(v > 1000 for v in FIFA_DATA.values())
      print(f'All above 1000: {all_positive}')
      "
    Expected Result: Total: 48, France: 1877.32, NZ: 1281.57, Range: ~595.75, All above 1000: True
    Failure Indicators: Count ≠ 48, wrong points, negative values
    Evidence: .omo/evidence/task-4-fifa-data.txt

  Scenario: Cross-reference — all ISO3 codes match country map
    Tool: Bash
    Preconditions: src/fifa_data.py and src/country_map.py exist
    Steps:
      1. python -c "
      from src.fifa_data import FIFA_DATA
      from src.country_map import COUNTRY_MAP
      fifa_codes = set(FIFA_DATA.keys())
      map_codes = set(entry['iso3'] for entry in COUNTRY_MAP)
      missing = fifa_codes - map_codes
      extra = map_codes - fifa_codes
      print(f'FIFA codes not in map: {missing}')
      print(f'Map codes not in FIFA: {extra}')
      print('CROSS_REF_OK' if not missing and not extra else 'CROSS_REF_FAIL')
      "
    Expected Result: Both sets empty; "CROSS_REF_OK"
    Failure Indicators: Any mismatched codes
    Evidence: .omo/evidence/task-4-cross-ref.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat: add FIFA April 2026 ranking data for 48 WC nations`
  - Files: `src/fifa_data.py`, `tests/test_fifa_data.py`

- [ ] 5. Economic Formula Engine

  **What to do**:
  - Create `src/formula.py` with the exact Bond Vigilantes model formula
  - Function: `compute_econ_score(pop, gdp, infl, unemp, rate, debt_gdp) -> float`
  - Formula: `max(log10(pop)-6, 0)^1.2 × (1+gdp/8) × 1/(1+infl/8) × (1-unemp) × 1/(1+rate/20) × 1/(0.8+debt_gdp/5)`
  - **Unit convention (CRITICAL — document in docstring)**:
    - `pop`: absolute number (e.g., 330000000 for 330M)
    - `gdp`, `infl`, `rate`: percentage (e.g., 3.5 for 3.5%, NOT 0.035)
    - `unemp`: decimal (e.g., 0.04 for 4%, NOT 4.0) — note this differs from GDP/Infl/Rate
    - `debt_gdp`: ratio (e.g., 0.80 for 80%, NOT 80)
  - Implement `POP_CLAMP` = `max(log10(pop)-6, 0)` for Pop < 1M nations (Curacao)
  - Write `tests/test_formula.py` FIRST (TDD):
    - Test: hand-calculated US case — verify against manual calculation (~2.19)
    - Test: Curacao Pop < 1M clamp → population term = 0, NOT NaN
    - Test: negative GDP (Qatar -8.6%) → doesn't crash
    - Test: zero policy rate (Switzerland) → term = 1.0
    - Test: high inflation penalty (Turkey 40%) → term ≈ 0.167
    - Test: Japan high debt (255%) → term ≈ 0.76 (mild per thesis)
    - Test: France vs New Zealand → France econ score >> New Zealand
    - Test: all computed scores are real numbers (no NaN, no Inf)

  **Must NOT do**:
  - Do NOT change formula weights or structure — exact replication required
  - Do NOT add home advantage factor — neutral venue model per thesis

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure mathematical function — deterministic, well-specified formula, no external deps
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4)
  - **Blocks**: Tasks 9, 10
  - **Blocked By**: Task 2 (for test data — can use hardcoded values as stand-in)

  **References** (CRITICAL):

  **Model Reference** (from `model_thesis`):
  ```
  Econ Model: (LOG10(Pop)-6)^1.2 × (1+GDP/8) × 1/(1+Infl/8) × (1-Unemp) × 1/(1+Rate/20) × 1/(0.8+Debt÷GDP/5)
  ```

  **Manual calculation for US** (golden test case):
  - pop=340,000,000 → log10=8.53 → (8.53-6)^1.2 = (2.53)^1.2 ≈ 3.05
  - gdp=2.5 → (1+2.5/8) = 1.3125
  - infl=3.0 → 1/(1+3.0/8) = 1/1.375 = 0.7273
  - unemp=0.04 → (1-0.04) = 0.96
  - rate=5.0 → 1/(1+5.0/20) = 1/1.25 = 0.8
  - debt_gdp=1.10 → 1/(0.8+1.10/5) = 1/1.02 = 0.9804
  - **Expected econ score**: 3.05 × 1.3125 × 0.7273 × 0.96 × 0.8 × 0.9804 ≈ 2.19

  **WHY**: The manual calculation is the golden test — validates unit conventions and formula correctness before any API data enters the pipeline.

  **Acceptance Criteria**:
  - [ ] File created: `src/formula.py`
  - [ ] `python -m pytest tests/test_formula.py -v` → PASS (8+ tests, 0 failures)
  - [ ] `python -c "from src.formula import compute_econ_score; s = compute_econ_score(340_000_000, 2.5, 3.0, 0.04, 5.0, 1.10); print(f'{s:.4f}')"` → ~2.19

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — US econ score matches manual calculation
    Tool: Bash
    Preconditions: src/formula.py exists
    Steps:
      1. python -c "
      from src.formula import compute_econ_score
      score = compute_econ_score(340_000_000, 2.5, 3.0, 0.04, 5.0, 1.10)
      expected = 2.19
      diff = abs(score - expected)
      print(f'US econ score: {score:.4f} (expected ~{expected:.2f}, diff={diff:.4f})')
      print('MATCH' if diff < 0.1 else 'MISMATCH')
      "
    Expected Result: Score ~2.19, diff < 0.1, "MATCH"
    Evidence: .omo/evidence/task-5-us-econ-score.txt

  Scenario: Edge case — Curacao (Pop < 1M) doesn't produce NaN
    Tool: Bash
    Preconditions: src/formula.py exists
    Steps:
      1. python -c "
      from src.formula import compute_econ_score
      score = compute_econ_score(150_000, 1.5, 3.0, 0.08, 3.5, 0.60)
      import math
      is_nan = math.isnan(score) if hasattr(math, 'isnan') else score != score
      print(f'Curacao econ score: {score:.4f}')
      print('OK' if not is_nan and score >= 0 else 'FAIL')
      "
    Expected Result: Score is 0.0 (population clamp) or very small; not NaN; not negative
    Evidence: .omo/evidence/task-5-curacao-no-nan.txt

  Scenario: Edge case — negative GDP (Qatar) doesn't crash
    Tool: Bash
    Preconditions: src/formula.py exists
    Steps:
      1. python -c "
      from src.formula import compute_econ_score
      score = compute_econ_score(2_900_000, -8.6, 2.0, 0.001, 5.5, 0.40)
      print(f'Qatar econ score: {score:.4f}')
      print('OK (not NaN)' if score == score else 'NaN')
      "
    Expected Result: Real number (possibly negative or small, but not NaN)
    Evidence: .omo/evidence/task-5-qatar-negative-gdp.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat: implement Bond Vigilantes economic formula engine`
  - Files: `src/formula.py`, `tests/test_formula.py`

- [ ] 6. IMF WEO Data Fetcher

  **What to do**:
  - Create `src/imf_fetcher.py` with functions to fetch IMF WEO 2026 economic data
  - Base URL: `https://www.imf.org/external/datamapper/api/v1/`
  - Indicators to fetch: `NGDP_RPCH` (GDP growth), `PCPIPCH` (inflation), `LUR` (unemployment), `GGXWDG_NGDP` (gov debt/GDP), `LP` (population)
  - Function: `fetch_imf_data(countries_iso3: list[str], year=2026) -> dict[str, dict]`
    - Returns dict keyed by ISO3 with sub-dict of metric → value
    - Handles missing values gracefully (IMF may return null for some countries/years)
  - Function: `parse_imf_response(raw_json) -> dict` — extract values from API response
  - Add `time.sleep(0.3)` between API calls (5 indicators × 1 batch call = ~1.5s total)
  - Write `tests/test_imf_fetcher.py` FIRST (TDD):
    - Test: mock API response → correct parsing of GDP, inflation, unemp, debt, pop
    - Test: null value in API → returned as None with warning
    - Test: HTTP 500 error → graceful error, returns partial data
    - Test: all 48 ISO3 codes present in returned data
    - Test: 2026 year parameter is passed correctly in API URL
    - Test: timeout handling (requests timeout=10s)

  **Must NOT do**:
  - Do NOT use `imfp` library (version instability — use plain `requests`)
  - Do NOT scrape IMF website — use DataMapper API v1 only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: External API integration — requires HTTP request handling, error states, mock setup
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 7, 8)
  - **Blocks**: Task 9
  - **Blocked By**: Task 2 (needs ISO3 country codes list)

  **References** (CRITICAL):

  **API Reference** (from librarian research):
  - Base URL: `https://www.imf.org/external/datamapper/api/v1/`
  - Example: `https://www.imf.org/external/datamapper/api/v1/NGDP_RPCH?periods=2026`
  - Response shape: `{"values": {"NGDP_RPCH": {"USA": {"2026": 2.5}, "FRA": {"2026": 1.2}, ...}}}`
  - All indicators endpoint: `https://www.imf.org/external/datamapper/api/v1/indicators`
  - **No auth required** — free and open API
  - Indicator codes: `NGDP_RPCH` (GDP growth), `PCPIPCH` (inflation avg CPI), `LUR` (unemployment rate), `GGXWDG_NGDP` (gov debt %GDP), `LP` (population millions)
  - **Unit warning**: IMF returns `LP` in millions (e.g., 340.0 for USA), `LUR` as percentage (e.g., 4.0 for 4%), `GGXWDG_NGDP` as percentage (e.g., 110.0 for 110%)
  - MUST convert: `LP` millions → absolute (×1,000,000), `LUR` % → decimal (÷100), `GGXWDG_NGDP` % → ratio (÷100)

  **WHY**: These are the exact API endpoints and response formats — the executor must handle the IMF's JSON structure correctly and apply the unit conversions for the formula.

  **Acceptance Criteria**:
  - [ ] File created: `src/imf_fetcher.py`
  - [ ] `python -m pytest tests/test_imf_fetcher.py -v` → PASS (6+ tests, 0 failures)
  - [ ] `python -c "from src.imf_fetcher import fetch_imf_data; d = fetch_imf_data(['USA'], 2026); print('USA' in d)"` → True (when API available)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — mock successful API response parsed correctly
    Tool: Bash
    Preconditions: src/imf_fetcher.py and tests/test_imf_fetcher.py exist
    Steps:
      1. python -m pytest tests/test_imf_fetcher.py::test_parse_valid_response -v 2>&1
    Expected Result: "1 passed" — mock response parsed correctly
    Evidence: .omo/evidence/task-6-mock-parse.txt

  Scenario: Error case — null value handling
    Tool: Bash
    Preconditions: tests/test_imf_fetcher.py exists
    Steps:
      1. python -m pytest tests/test_imf_fetcher.py::test_null_value -v 2>&1
    Expected Result: "1 passed" — null handled as None with warning
    Evidence: .omo/evidence/task-6-null-handling.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat: add IMF WEO DataMapper API fetcher for economic indicators`
  - Files: `src/imf_fetcher.py`, `tests/test_imf_fetcher.py`

- [ ] 7. BIS Policy Rate Fetcher

  **What to do**:
  - Create `src/bis_fetcher.py` with functions to fetch BIS central bank policy rates
  - Base URL: `https://stats.bis.org/api/v1/data/WS_CBPOL`
  - Key format: `M.{ISO3}` for monthly data
  - Function: `fetch_policy_rate(iso3: str) -> float | None`
    - Returns the latest monthly policy rate value
    - Returns None if BIS doesn't have data for this country
  - Function: `fetch_all_policy_rates(countries_iso3: list[str]) -> dict[str, float | None]`
    - Batch fetch with `time.sleep(0.3)` between calls
    - Log WARNING for countries with no BIS data
  - Known coverage gap: BIS covers ~50 countries — ~20 World Cup nations will return None
  - Write `tests/test_bis_fetcher.py` FIRST (TDD):
    - Test: mock BIS CSV response → correct rate extraction
    - Test: BIS returns no data for country → returns None
    - Test: HTTP 404 → returns None gracefully
    - Test: multiple ISO3 batch → correct dict structure
    - Test: timeout handling (requests timeout=10s)

  **Must NOT do**:
  - Do NOT scrape central bank websites — BIS API only
  - Do NOT crash when BIS has no data for a country — return None, let aggregation handle fallback

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: External API integration with CSV parsing, error states, batch handling
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 8)
  - **Blocks**: Task 9
  - **Blocked By**: Task 2 (needs ISO3 codes)

  **References** (CRITICAL):

  **API Reference** (from librarian research):
  - Endpoint: `https://stats.bis.org/api/v1/data/WS_CBPOL/M.{ISO3}?lastNObservations=1`
  - Headers: `Accept: text/csv`
  - Response: CSV with columns `TIME_PERIOD, OBS_VALUE`
  - Example: `https://stats.bis.org/api/v1/data/WS_CBPOL/M.US?lastNObservations=1` → returns latest US Fed funds rate
  - **No auth required**
  - Rate limit: None published, but add 0.3s sleep between calls

  **Coverage reference**: BIS CBPOL dataset covers 40+ advanced and emerging economies. Known gaps for World Cup 2026: Curaçao, Ivory Coast, Uzbekistan, Iraq, Jordan, Haiti, Cape Verde, Ghana, DR Congo, Panama, Bosnia, Qatar (may or may not have data). For these, return None.

  **WHY**: The BIS API format and coverage gaps are critical — the executor must handle missing data gracefully and NOT crash when 20+ nations return no data.

  **Acceptance Criteria**:
  - [ ] File created: `src/bis_fetcher.py`
  - [ ] `python -m pytest tests/test_bis_fetcher.py -v` → PASS (5+ tests, 0 failures)
  - [ ] Mock test verifies None return for uncovered countries

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — mock US policy rate fetched correctly
    Tool: Bash
    Preconditions: src/bis_fetcher.py, tests/test_bis_fetcher.py exist
    Steps:
      1. python -m pytest tests/test_bis_fetcher.py::test_parse_valid_csv -v 2>&1
    Expected Result: "1 passed" — rate extracted from mock CSV
    Evidence: .omo/evidence/task-7-mock-rate.txt

  Scenario: Error case — missing country returns None
    Tool: Bash
    Preconditions: tests/test_bis_fetcher.py exists
    Steps:
      1. python -m pytest tests/test_bis_fetcher.py::test_missing_country -v 2>&1
    Expected Result: "1 passed" — returns None without exception
    Evidence: .omo/evidence/task-7-missing-country.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat: add BIS policy rate fetcher with graceful missing-data handling`
  - Files: `src/bis_fetcher.py`, `tests/test_bis_fetcher.py`

- [ ] 8. Data Validation Schema + Module

  **What to do**:
  - Create `src/validation.py` defining the expected data schema for all economic metrics
  - Define `EconData` dataclass/typed dict: `iso3`, `pop`, `gdp`, `infl`, `unemp`, `rate`, `debt_gdp`, `source` (str: "imf"/"bis"/"wb"/"fallback")
  - Define `validate_econ_data(data: list[EconData])` → checks: 48 nations present, no None values, realistic ranges
  - Range checks: pop > 0, gdp between -20 and +30, infl between -5 and 200, unemp between 0.001 and 0.5, rate between -2 and 50, debt_gdp between 0 and 3.0
  - Log WARNING (not crash) for missing data — return list of warnings alongside validated data
  - Write `tests/test_validation.py` FIRST (TDD):
    - Test: valid data passes validation → returns empty warnings list
    - Test: missing nation → warning logged, 47 nations remain
    - Test: extreme but valid value (Turkey infl=40) → passes validation
    - Test: impossible value (unemp=-0.1) → warning logged
    - Test: all 48 nations validated against COUNTRY_MAP ISO3 codes
    - Test: Curacao (pop=150K) passes validation → no NaN warning

  **Must NOT do**:
  - Do NOT crash/throw on validation warnings — log and continue
  - Do NOT validate against actual API data (that's Task 9) — validate the schema/structure only

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure validation logic — defined rules, no external deps, minimal code
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 6, 7)
  - **Blocks**: Task 9
  - **Blocked By**: Task 2 (needs ISO3 list)

  **References**: N/A — straightforward validation logic with explicit rules above.

  **Acceptance Criteria**:
  - [ ] File created: `src/validation.py`
  - [ ] `python -m pytest tests/test_validation.py -v` → PASS (6+ tests, 0 failures)

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — valid data passes silently
    Tool: Bash
    Preconditions: src/validation.py exists
    Steps:
      1. python -c "
      from src.validation import validate_econ_data, EconData
      data = [EconData(iso3='USA', pop=340_000_000, gdp=2.5, infl=3.0, unemp=0.04, rate=5.0, debt_gdp=1.10, source='imf')]
      warnings = validate_econ_data(data)
      print(f'Warnings: {len(warnings)}')
      print('PASS' if len(warnings) == 0 else 'FAIL')
      "
    Expected Result: Warnings: 0, PASS
    Evidence: .omo/evidence/task-8-validation-pass.txt

  Scenario: Edge case — extreme values flagged but not crashed
    Tool: Bash
    Preconditions: src/validation.py exists
    Steps:
      1. python -c "
      from src.validation import validate_econ_data, EconData
      data = [EconData(iso3='TUR', pop=85_000_000, gdp=3.0, infl=40.0, unemp=0.10, rate=35.0, debt_gdp=0.40, source='imf')]
      warnings = validate_econ_data(data)
      print(f'Warnings: {len(warnings)}')
      print('OK (no crash)' if len(warnings) >= 0 else 'FAIL')
      "
    Expected Result: Warnings may be >0 but no crash
    Evidence: .omo/evidence/task-8-extreme-values.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat: add economic data validation schema`
  - Files: `src/validation.py`, `tests/test_validation.py`

- [ ] 9. Data Aggregation + Normalization Pipeline

  **What to do**:
  - Create `src/aggregate.py` — the central data pipeline that merges all sources
  - Function: `build_dataset(imf_data, bis_rates, fifa_data, country_map) -> pd.DataFrame`
    - Merge IMF economic data + BIS policy rates + FIFA rankings into one DataFrame
    - Index by ISO3, columns: `pop`, `gdp`, `infl`, `unemp`, `rate`, `debt_gdp`, `fifa_points`
  - **Unit conversions** (CRITICAL — document every conversion):
    - IMF `LP` (millions) → absolute population (× 1,000,000)
    - IMF `LUR` (percentage) → decimal (÷ 100)
    - IMF `GGXWDG_NGDP` (percentage) → ratio (÷ 100)
    - BIS rate → pass through as percentage (already in % form)
  - **Missing data fallback**:
    - If BIS rate is None: use World Bank fallback or median of similar-ranked economies
    - If any IMF metric is None: log WARNING, use World Bank `wbgapi` fallback for that metric
    - If fallback also fails: log ERROR, exclude country (warn user)
  - Function: `normalize_scores(df) -> pd.DataFrame`:
    - Min-max normalize FIFA points: `(x - min) / (max - min)` → all 48 teams on [0, 1]
    - Min-max normalize econ scores: `(x - min) / (max - min)` → all 48 teams on [0, 1]
    - Add columns: `norm_fifa`, `norm_econ`
  - Write `tests/test_aggregate.py` FIRST (TDD):
    - Test: merge 3 sources → correct 48-row DataFrame
    - Test: unit conversions correct (LP millions → absolute, LUR % → decimal, debt % → ratio)
    - Test: missing BIS rate → fallback applied, WARNING logged
    - Test: missing IMF metric → World Bank fallback attempted
    - Test: min-max normalization produces 0.0 for worst, 1.0 for best
    - Test: normalization is reproducible (same input → same output)

  **Must NOT do**:
  - Do NOT drop countries with missing data — log warnings and use fallbacks
  - Do NOT apply the formula here — that's Task 5's job (aggregation calls formula.py)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex data pipeline — merging multiple API sources, unit conversions, fallback logic, pandas operations
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (single task — unavoidable aggregation bottleneck)
  - **Blocks**: Task 10
  - **Blocked By**: Tasks 4, 5, 6, 7, 8

  **References** (CRITICAL):

  **Unit Conversion Reference** (from IMF API research):
  - IMF `LP`: "Population (millions of people)" → returned as 340.0 for USA → MUST multiply by 1,000,000
  - IMF `LUR`: "Unemployment rate (percent)" → returned as 4.0 for USA → MUST divide by 100 to get 0.04
  - IMF `GGXWDG_NGDP`: "General government gross debt (% of GDP)" → returned as 110.0 for USA → MUST divide by 100 to get 1.10
  - IMF `NGDP_RPCH` and `PCPIPCH`: already in percentage form → pass through as-is

  **Formula input reference** (from Task 5): `compute_econ_score(pop, gdp, infl, unemp, rate, debt_gdp)` expects:
  - pop: absolute, gdp/infl/rate: %, unemp: decimal, debt_gdp: ratio

  **WHY**: A single wrong unit conversion (e.g., passing 4.0 instead of 0.04 for unemployment) produces catastrophic results. These conversions are the bridge between raw API data and the formula.

  **Acceptance Criteria**:
  - [ ] File created: `src/aggregate.py`
  - [ ] `python -m pytest tests/test_aggregate.py -v` → PASS (6+ tests, 0 failures)
  - [ ] Mock aggregation test produces DataFrame with 48 rows and all required columns

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — merge produces correct DataFrame
    Tool: Bash
    Preconditions: mock data available in test fixtures
    Steps:
      1. python -m pytest tests/test_aggregate.py::test_merge_dataset -v 2>&1
    Expected Result: "1 passed" — 48 rows, all columns present
    Evidence: .omo/evidence/task-9-merge-dataset.txt

  Scenario: Unit conversion — verify LUR decimal conversion
    Tool: Bash
    Preconditions: tests/test_aggregate.py exists
    Steps:
      1. python -m pytest tests/test_aggregate.py::test_unit_conversions -v 2>&1
    Expected Result: "1 passed" — LUR 4.0 → 0.04; GGXWDG 110.0 → 1.10; LP 340.0 → 340000000
    Evidence: .omo/evidence/task-9-unit-conversions.txt

  Scenario: Normalization — min/max are 0.0 and 1.0
    Tool: Bash
    Preconditions: tests/test_aggregate.py exists
    Steps:
      1. python -m pytest tests/test_aggregate.py::test_normalization_range -v 2>&1
    Expected Result: "1 passed" — norm_fifa and norm_econ both in [0, 1]
    Evidence: .omo/evidence/task-9-normalization-range.txt
  ```

  **Commit**: YES (individual — this is the central integration point)
  - Message: `feat: add data aggregation pipeline with unit conversions and normalization`
  - Files: `src/aggregate.py`, `tests/test_aggregate.py`

- [ ] 10. Prediction Engine (Blending, xG, Noise, Match Results)

  **What to do**:
  - Create `src/predict.py` — the core prediction engine
  - Function: `compute_blended_score(norm_fifa, norm_econ) -> float`:
    - `0.5 * norm_fifa + 0.5 * norm_econ` (hardcoded 50/50)
  - Function: `blended_to_xg(blended_score) -> float`:
    - `xG = blended_score * 4` (maps [0,1] to [0,4] expected goals)
  - Function: `apply_noise(xg, seed=None) -> float`:
    - `xG_noisy = xG + random.gauss(0, 0.3)` with optional seed
    - Clamp result to [0, 4] range
  - Function: `predict_match(team_a_iso3, team_b_iso3, dataset, seed=None) -> dict`:
    - Look up both teams in dataset
    - Compute blended scores → xG → add noise → round to integers
    - Return: `{team_a: str, team_b: str, team_a_xg: float, team_b_xg: float, predicted_score: str (e.g. "2-1"), team_a_blended: float, team_b_blended: float, team_a_econ: float, team_b_econ: float, team_a_fifa: float, team_b_fifa: float}`
  - Function: `predict_all_upcoming(matches, dataset, seed=None) -> list[dict]`:
    - Iterate all upcoming matches, predict each
  - Write `tests/test_predict.py` FIRST (TDD):
    - Test: 50/50 blend of (0.8, 0.6) → 0.7
    - Test: blend of (0.0, 0.0) → 0.0, blend of (1.0, 1.0) → 1.0
    - Test: blended_to_xg(0.5) → 2.0; blended_to_xg(1.0) → 4.0; blended_to_xg(0.0) → 0.0
    - Test: apply_noise with seed=42 → reproducible output
    - Test: apply_noise clamps to [0, 4] even with extreme noise
    - Test: France (best) vs New Zealand (worst) → France wins by multiple goals
    - Test: USA vs Canada (similar strength) → close match, possibly draw
    - Test: predict_all_upcoming with 10 matches → returns 10 predictions
    - Test: reproducibility — same seed → same predictions

  **Must NOT do**:
  - Do NOT run Monte Carlo simulation — single pass with Gaussian noise only
  - Do NOT change 50/50 blend weights or σ=0.3 noise — hardcoded per thesis
  - Do NOT add home advantage — neutral venue model

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Core prediction logic — blending, statistical noise, match result generation, comprehensive edge case testing
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (single task — depends on aggregated dataset from Task 9)
  - **Blocks**: Tasks 11, 12
  - **Blocked By**: Tasks 3, 9

  **References** (CRITICAL):

  **Model Reference** (from thesis): "50/50 blend between a normalised FIFA points score, and a normalised economic metric score"
  **Expected goals reference**: "an expected goals number is produced to predict the result of the game"
  **Randomness reference**: "sprinkled in a little bit of randomness"
  **Result format reference**: Thesis shows "2-0 to the hosts" — integer score predictions

  **WHY**: This is the core of the entire project — the blending, xG conversion, and noise model must match the thesis interpretation exactly.

  **Acceptance Criteria**:
  - [ ] File created: `src/predict.py`
  - [ ] `python -m pytest tests/test_predict.py -v` → PASS (9+ tests, 0 failures)
  - [ ] `python -c "from src.predict import predict_match; ..."` → returns valid prediction dict

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — France vs New Zealand prediction is lopsided
    Tool: Bash
    Preconditions: mock dataset with France (fifa=1877, high econ) and NZ (fifa=1282, low econ)
    Steps:
      1. python -m pytest tests/test_predict.py::test_lopsided_match -v 2>&1
    Expected Result: "1 passed" — France predicted to win by 2+ goals
    Evidence: .omo/evidence/task-10-lopsided-match.txt

  Scenario: Reproducibility — same seed = same output
    Tool: Bash
    Preconditions: tests/test_predict.py exists
    Steps:
      1. python -m pytest tests/test_predict.py::test_reproducibility -v 2>&1
    Expected Result: "1 passed" — seed=42 produces identical predictions on consecutive calls
    Evidence: .omo/evidence/task-10-reproducibility.txt

  Scenario: Edge case — noise clamped to [0, 4]
    Tool: Bash
    Preconditions: tests/test_predict.py exists
    Steps:
      1. python -m pytest tests/test_predict.py::test_noise_clamp -v 2>&1
    Expected Result: "1 passed" — xG never exceeds [0, 4] range
    Evidence: .omo/evidence/task-10-noise-clamp.txt
  ```

  **Commit**: YES (individual — critical business logic)
  - Message: `feat: add prediction engine with 50/50 blending and Gaussian noise`
  - Files: `src/predict.py`, `tests/test_predict.py`

- [ ] 11. CLI Interface + Main Entry Point

  **What to do**:
  - Create `src/cli.py` — the command-line interface using `argparse`
  - Arguments:
    - `--seed` (int, default=42): Random seed for reproducibility
    - `--cutoff-date` (str, default=today): ISO date for "upcoming matches" filter
    - `--output-dir` (str, default="./output"): Output directory for CSV/Excel
    - `--no-fetch` (flag): Skip API calls, use cached/test data only
  - Main function `main()` orchestrates the full pipeline:
    1. Load country map → schedule → FIFA data (always)
    2. If `--no-fetch`: load mock/cached economic data; else: fetch from IMF + BIS APIs
    3. Aggregate data → validate → normalize
    4. Compute predictions for upcoming matches
    5. Call output generators (CSV + Excel)
    6. Print summary: "Generated N predictions. Output: output/world_cup_predictions.{csv,xlsx}"
  - Entry point: `if __name__ == "__main__": main()`
  - Add `pyproject.toml` entry: `[project.scripts] predict = "src.cli:main"`
  - Write `tests/test_cli.py` FIRST (TDD):
    - Test: `--help` prints usage
    - Test: `--seed 42 --no-fetch` runs successfully with mock data
    - Test: `--cutoff-date 2026-06-20` filters correctly
    - Test: missing output dir → auto-created
    - Test: invalid date format → argparse error

  **Must NOT do**:
  - Do NOT hardcode paths — use `--output-dir`
  - Do NOT run API calls by default in tests — use `--no-fetch` in tests

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard CLI with argparse — well-understood pattern, straightforward integration
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 12)
  - **Parallel Group**: Wave 5 (with Task 12)
  - **Blocks**: None (final integration)
  - **Blocked By**: Task 10 (needs prediction engine)

  **References**:
  - `argparse` docs: `https://docs.python.org/3/library/argparse.html`
  - `pyproject.toml` scripts: PEP 621 `[project.scripts]` section

  **Acceptance Criteria**:
  - [ ] File created: `src/cli.py`
  - [ ] `python -m pytest tests/test_cli.py -v` → PASS (5+ tests, 0 failures)
  - [ ] `python -m src.cli --help` prints usage message
  - [ ] `python -m src.cli --seed 42 --no-fetch --output-dir /tmp/test_output` runs to completion

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — script runs end-to-end with mock data
    Tool: Bash
    Preconditions: All src/ modules exist, mock data available
    Steps:
      1. python -m src.cli --seed 42 --no-fetch --output-dir /tmp/test_wc_output 2>&1
    Expected Result: Prints summary: "Generated N predictions. Output: /tmp/test_wc_output/world_cup_predictions.csv, /tmp/test_wc_output/world_cup_predictions.xlsx"
    Failure Indicators: Traceback, ImportError, FileNotFoundError
    Evidence: .omo/evidence/task-11-e2e-run.txt

  Scenario: Invalid date → argparse error
    Tool: Bash
    Preconditions: src/cli.py exists
    Steps:
      1. python -m src.cli --cutoff-date "not-a-date" 2>&1; echo "EXIT: $?"
    Expected Result: Non-zero exit code, error message about invalid date format
    Evidence: .omo/evidence/task-11-invalid-date.txt
  ```

  **Commit**: YES (groups with Task 12 in Wave 5)
  - Message: `feat: add CLI interface with --seed, --cutoff-date, --no-fetch flags`
  - Files: `src/cli.py`, `tests/test_cli.py`

- [ ] 12. CSV + Excel Output Generator

  **What to do**:
  - Create `src/output.py` with functions to generate CSV and Excel files
  - Function: `generate_csv(predictions: list[dict], output_dir: str) -> str`:
    - Write `world_cup_predictions.csv`
    - Columns: `match_number`, `group`, `date`, `team_a`, `team_b`, `predicted_score`, `team_a_xg`, `team_b_xg`, `team_a_econ_score`, `team_b_econ_score`, `team_a_fifa_score`, `team_b_fifa_score`, `team_a_blended`, `team_b_blended`
    - Use `csv.DictWriter` from stdlib
    - Return file path
  - Function: `generate_excel(predictions: list[dict], output_dir: str) -> str`:
    - Write `world_cup_predictions.xlsx`
    - Same columns as CSV
    - Add formatting: header row bold, column auto-width, number formatting (2 decimal places for xG/scores)
    - Add a second sheet "Model Parameters" with: blend weights (50/50), noise σ (0.3), seed used, cutoff date, data sources
    - Use `openpyxl`
    - Return file path
  - Function: `generate_all(predictions, output_dir)` → calls both, returns tuple of paths
  - Write `tests/test_output.py` FIRST (TDD):
    - Test: CSV file created and has correct headers
    - Test: CSV row count matches predictions list length
    - Test: CSV is valid (parseable by `csv.DictReader`)
    - Test: Excel file created and openable by `openpyxl`
    - Test: Excel has 2 sheets ("Predictions", "Model Parameters")
    - Test: Excel header row is bold
    - Test: output dir auto-created if missing

  **Must NOT do**:
  - Do NOT add charts/graphs to Excel — data only
  - Do NOT add conditional formatting — simple formatting only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Dual output format (CSV + Excel) with formatting logic — moderate complexity
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 11)
  - **Parallel Group**: Wave 5 (with Task 11)
  - **Blocks**: None
  - **Blocked By**: Task 3 (needs schedule for group/date info), Task 10 (needs predictions)

  **References**:
  - `csv` module: `https://docs.python.org/3/library/csv.html` — `csv.DictWriter`
  - `openpyxl` docs: `https://openpyxl.readthedocs.io/en/stable/` — Workbook, Worksheet, styles
  - Output schema defined in "Must Have" section above

  **Acceptance Criteria**:
  - [ ] File created: `src/output.py`
  - [ ] `python -m pytest tests/test_output.py -v` → PASS (7+ tests, 0 failures)
  - [ ] Generated CSV is valid: `python -c "import csv; rows=list(csv.DictReader(open('output/world_cup_predictions.csv'))); assert len(rows) > 0; print('CSV OK:', len(rows), 'rows')"`
  - [ ] Generated Excel is valid: `python -c "import openpyxl; wb=openpyxl.load_workbook('output/world_cup_predictions.xlsx'); print('Sheets:', wb.sheetnames); assert 'Predictions' in wb.sheetnames"`

  **QA Scenarios (MANDATORY)**:

  ```
  Scenario: Happy path — CSV output is valid and complete
    Tool: Bash
    Preconditions: src/output.py and mock predictions exist
    Steps:
      1. python -m pytest tests/test_output.py::test_csv_output -v 2>&1
    Expected Result: "1 passed" — CSV valid, correct headers, row count matches
    Evidence: .omo/evidence/task-12-csv-valid.txt

  Scenario: Happy path — Excel output has both sheets and formatting
    Tool: Bash
    Preconditions: tests/test_output.py exists
    Steps:
      1. python -m pytest tests/test_output.py::test_excel_output -v 2>&1
    Expected Result: "1 passed" — 2 sheets, header bold, data present
    Evidence: .omo/evidence/task-12-excel-valid.txt

  Scenario: Edge case — output dir auto-created
    Tool: Bash
    Preconditions: tests/test_output.py exists
    Steps:
      1. python -m pytest tests/test_output.py::test_auto_create_dir -v 2>&1
    Expected Result: "1 passed" — directory created automatically, no FileNotFoundError
    Evidence: .omo/evidence/task-12-auto-create-dir.txt
  ```

  **Commit**: YES (groups with Task 11 in Wave 5)
  - Message: `feat: add CSV + Excel output generator with formatted thesis`
  - Files: `src/output.py`, `tests/test_output.py`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.omo/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [12/12] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m pytest tests/ -v` + `python -m py_compile src/*.py`. Review all source files for: bare `except:`, `print()` in library code (not CLI), commented-out code, unused imports, missing docstrings on public functions. Check AI slop: excessive comments, over-abstraction, generic variable names.
  Output: `Tests [N pass/N fail] | Compile [PASS/FAIL] | Files [N clean/N issues] | VERDICT: APPROVE/REJECT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Start from clean state. Run `python -m src.cli --seed 42 --no-fetch --output-dir /tmp/qa_output`. Verify:
  1. Script completes without errors
  2. CSV file exists and has correct schema (14 columns)
  3. Excel file exists, opens correctly, has 2 sheets
  4. All predicted scores are in valid format (e.g., "2-1", "0-0")
  5. No NaN or None values in output
  6. Predictions only include group stage matches (#9-72), no knockout matches
  Save evidence to `.omo/evidence/final-qa/`.
  Output: `E2E Run [PASS/FAIL] | CSV Valid [PASS/FAIL] | Excel Valid [PASS/FAIL] | Scores Valid [PASS/FAIL] | VERDICT: APPROVE/REJECT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git diff or file comparison). Verify 1:1 — everything specified was built (no missing modules), nothing beyond spec was built (no scope creep). Check "Must NOT do" compliance per task. Detect cross-task contamination. Flag unaccounted files.
  Output: `Tasks [12/12 compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT: APPROVE/REJECT`

---

## Commit Strategy

All commits use format: `type(scope): description`

- **Wave 1**: Single commit grouping Tasks 1-5
  - `chore: initialize project with core data modules and formula engine`
  - Files: `pyproject.toml`, `src/__init__.py`, `tests/__init__.py`, `tests/conftest.py`, `src/country_map.py`, `src/schedule.py`, `src/fifa_data.py`, `src/formula.py`, all `tests/test_*.py` files, `.gitignore`, `README.md`
  - Pre-commit: `python -m pytest tests/ -v --tb=short`

- **Wave 2**: Single commit grouping Tasks 6-8
  - `feat: add IMF and BIS data fetchers with validation`
  - Files: `src/imf_fetcher.py`, `src/bis_fetcher.py`, `src/validation.py`, `tests/test_imf_fetcher.py`, `tests/test_bis_fetcher.py`, `tests/test_validation.py`
  - Pre-commit: `python -m pytest tests/ -v --tb=short`

- **Wave 3 + Wave 4**: Single commit grouping Tasks 9-10 (sequential pipeline)
  - `feat: add data aggregation, normalization, and prediction engine`
  - Files: `src/aggregate.py`, `src/predict.py`, `tests/test_aggregate.py`, `tests/test_predict.py`
  - Pre-commit: `python -m pytest tests/ -v --tb=short`

- **Wave 5**: Single commit grouping Tasks 11-12
  - `feat: add CLI interface and CSV/Excel output generation`
  - Files: `src/cli.py`, `src/output.py`, `tests/test_cli.py`, `tests/test_output.py`
  - Pre-commit: `python -m pytest tests/ -v --tb=short`

- **Final Verification**: After F1-F4 all APPROVE, tag as `v1.0.0`

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
python -m pytest tests/ -v
# Expected: ALL tests pass (0 failures)

# Run end-to-end with mock data
python -m src.cli --seed 42 --no-fetch --output-dir ./output
# Expected: "Generated N predictions. Output: output/world_cup_predictions.{csv,xlsx}"

# Validate CSV
python -c "import csv; rows=list(csv.DictReader(open('output/world_cup_predictions.csv'))); print(f'CSV: {len(rows)} rows, {len(rows[0])} cols')"
# Expected: ~64 rows (remaining group matches), 14 columns

# Validate Excel
python -c "import openpyxl; wb=openpyxl.load_workbook('output/world_cup_predictions.xlsx'); print(wb.sheetnames)"
# Expected: ['Predictions', 'Model Parameters']

# Reproducibility check
diff <(python -m src.cli --seed 42 --no-fetch --output-dir /tmp/run1 2>/dev/null && cat /tmp/run1/world_cup_predictions.csv) \
     <(python -m src.cli --seed 42 --no-fetch --output-dir /tmp/run2 2>/dev/null && cat /tmp/run2/world_cup_predictions.csv)
# Expected: no diff (identical output)
```

### Final Checklist
- [ ] All "Must Have" requirements present in implementation
- [ ] All "Must NOT Have" guardrails enforced (no Monte Carlo, no knockout, no scraping, no viz, no pandas-datareader)
- [ ] `python -m pytest tests/ -v` → ALL tests pass
- [ ] Script runs end-to-end in <60 seconds
- [ ] CSV and Excel outputs are valid and parseable
- [ ] Reproducible output with `--seed 42`
- [ ] Only group stage matches #9-72 in output (no played matches, no knockout)
- [ ] All 48 nations have complete data (with logged warnings for any gaps)
- [ ] Formula implementation matches manual calculation (US econ score ≈ 2.19)
- [ ] Curacao (Pop < 1M) handled without NaN

