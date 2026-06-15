# World Cup 2026 Macro-Football Predictor & Betting Research System

> **Phase 1 — MVP**: A quantitative model blending FIFA rankings with macroeconomic fundamentals to forecast World Cup match outcomes, combined with a positive-EV betting engine that compares model probabilities against Bet365 odds.

---

## Current Predictions (13 June 2026)

68 remaining group stage matches predicted. Model run at market close 13 June 2026.
How to read this table:
• **Home / Away** — the two teams in the fixture. "Home" is listed first by convention; no home advantage is applied.
• **Score** — the model's predicted final scoreline. Each team's expected goals (xG) is rounded to the nearest integer after adding a small random noise term (σ = 0.3) to simulate real-world variance.
• **xG_H / xG_A** — expected goals for each team before rounding. A team with xG 2.8 is expected to score roughly 3 goals; a team with xG 0.3 is expected to score roughly 0. The gap between the two xG values indicates how one-sided the match is expected to be.
• **Favorite** — the team with the higher blended FIFA + economic score. "Draw" appears when the xG values are nearly identical.

| # | Date | Grp | Home | Away | Score | xG_H | xG_A | Favorite |
|---|------|-----|------|------|-------|------|------|----------|
| 5 | 2026-06-13 | B | QAT | CHE | 1-2 | 0.5 | 2.5 | CHE |
| 6 | 2026-06-13 | C | BRA | MAR | 3-3 | 2.9 | 2.7 | BRA |
| 7 | 2026-06-13 | C | HTI | SCO | 0-1 | 0.0 | 0.7 | SCO |
| 8 | 2026-06-13 | D | AUS | TUR | 2-1 | 1.7 | 1.5 | AUS |
| 9 | 2026-06-14 | E | DEU | CUW | 3-0 | 2.9 | 0.0 | DEU |
| 10 | 2026-06-14 | F | NLD | JPN | 2-2 | 2.2 | 2.2 | Draw |
| 11 | 2026-06-14 | E | CIV | ECU | 2-2 | 2.2 | 2.2 | Draw |
| 12 | 2026-06-14 | F | SWE | TUN | 2-1 | 1.8 | 0.9 | SWE |
| 13 | 2026-06-15 | H | ESP | CPV | 3-0 | 2.7 | 0.3 | ESP |
| 14 | 2026-06-15 | G | BEL | EGY | 2-2 | 2.0 | 1.8 | BEL |
| 15 | 2026-06-15 | H | SAU | URY | 2-1 | 1.8 | 1.1 | SAU |
| 16 | 2026-06-15 | G | IRN | NZL | 1-1 | 0.7 | 0.6 | IRN |
| 17 | 2026-06-16 | I | FRA | SEN | 3-3 | 3.2 | 2.7 | FRA |
| 18 | 2026-06-16 | I | IRQ | NOR | 1-2 | 1.3 | 1.7 | NOR |
| 19 | 2026-06-16 | J | ARG | DZA | 3-3 | 2.5 | 2.6 | Draw |
| 20 | 2026-06-16 | J | AUT | JOR | 2-1 | 1.9 | 0.7 | AUT |
| 21 | 2026-06-17 | K | PRT | COD | 2-3 | 2.0 | 2.8 | COD |
| 22 | 2026-06-17 | L | GBR | HRV | 3-4 | 2.8 | 4.0 | HRV |
| 23 | 2026-06-17 | L | GHA | PAN | 1-1 | 1.1 | 0.9 | GHA |
| 24 | 2026-06-17 | K | UZB | COL | 1-2 | 1.3 | 2.2 | COL |
| 25 | 2026-06-18 | A | CZE | ZAF | 2-1 | 1.6 | 0.8 | CZE |
| 26 | 2026-06-18 | B | CHE | BIH | 2-0 | 1.8 | 0.2 | CHE |
| 27 | 2026-06-18 | B | CAN | QAT | 1-0 | 1.4 | 0.4 | CAN |
| 28 | 2026-06-18 | A | MEX | KOR | 2-3 | 2.2 | 2.5 | KOR |
| 29 | 2026-06-19 | D | USA | AUS | 3-2 | 3.1 | 2.3 | USA |
| 30 | 2026-06-19 | C | SCO | MAR | 1-3 | 1.2 | 3.0 | MAR |
| 31 | 2026-06-19 | C | BRA | HTI | 2-0 | 2.4 | 0.2 | BRA |
| 32 | 2026-06-19 | D | TUR | PRY | 1-1 | 1.2 | 1.5 | PRY |
| 33 | 2026-06-20 | F | NLD | SWE | 3-1 | 2.6 | 1.3 | NLD |
| 34 | 2026-06-20 | E | DEU | CIV | 2-3 | 2.4 | 2.8 | CIV |
| 35 | 2026-06-20 | E | ECU | CUW | 2-0 | 2.3 | 0.0 | ECU |
| 36 | 2026-06-20 | F | TUN | JPN | 1-3 | 1.1 | 2.6 | JPN |
| 37 | 2026-06-21 | H | ESP | SAU | 3-1 | 3.2 | 1.4 | ESP |
| 38 | 2026-06-21 | G | BEL | IRN | 2-1 | 1.7 | 0.7 | BEL |
| 39 | 2026-06-21 | H | URY | CPV | 1-0 | 1.0 | 0.4 | URY |
| 40 | 2026-06-21 | G | NZL | EGY | 0-2 | 0.5 | 1.8 | EGY |
| 41 | 2026-06-22 | J | ARG | AUT | 2-2 | 2.2 | 1.7 | ARG |
| 42 | 2026-06-22 | I | FRA | IRQ | 3-1 | 3.2 | 0.6 | FRA |
| 43 | 2026-06-22 | I | NOR | SEN | 1-2 | 1.2 | 1.8 | SEN |
| 44 | 2026-06-22 | J | JOR | DZA | 1-2 | 0.6 | 2.5 | DZA |
| 45 | 2026-06-23 | K | PRT | UZB | 2-1 | 2.4 | 1.1 | PRT |
| 46 | 2026-06-23 | L | GBR | GHA | 2-1 | 2.1 | 1.2 | GBR |
| 47 | 2026-06-23 | L | PAN | HRV | 1-4 | 1.2 | 4.0 | HRV |
| 48 | 2026-06-23 | K | COL | COD | 2-3 | 2.1 | 2.7 | COD |
| 49 | 2026-06-24 | B | CHE | CAN | 2-2 | 2.1 | 2.0 | Draw |
| 50 | 2026-06-24 | B | BIH | QAT | 1-0 | 0.7 | 0.4 | BIH |
| 51 | 2026-06-24 | C | SCO | BRA | 1-3 | 0.6 | 2.8 | BRA |
| 52 | 2026-06-24 | C | MAR | HTI | 3-0 | 3.4 | 0.2 | MAR |
| 53 | 2026-06-24 | A | CZE | MEX | 1-3 | 1.4 | 2.6 | MEX |
| 54 | 2026-06-24 | A | ZAF | KOR | 1-2 | 1.2 | 1.9 | KOR |
| 55 | 2026-06-25 | E | ECU | DEU | 2-3 | 1.6 | 2.9 | DEU |
| 56 | 2026-06-25 | E | CUW | CIV | 0-2 | 0.4 | 2.3 | CIV |
| 57 | 2026-06-25 | F | JPN | SWE | 2-2 | 2.2 | 1.5 | JPN |
| 58 | 2026-06-25 | F | TUN | NLD | 1-2 | 1.2 | 1.9 | NLD |
| 59 | 2026-06-25 | D | TUR | USA | 1-3 | 0.8 | 3.0 | USA |
| 60 | 2026-06-25 | D | PRY | AUS | 1-1 | 1.5 | 1.4 | Draw |
| 61 | 2026-06-26 | I | SEN | IRQ | 2-1 | 1.8 | 0.5 | SEN |
| 62 | 2026-06-26 | I | NOR | FRA | 1-3 | 1.1 | 3.2 | FRA |
| 63 | 2026-06-26 | H | CPV | SAU | 0-2 | 0.5 | 1.5 | SAU |
| 64 | 2026-06-26 | H | URY | ESP | 1-3 | 1.4 | 3.2 | ESP |
| 65 | 2026-06-26 | G | EGY | IRN | 2-1 | 2.0 | 1.5 | EGY |
| 66 | 2026-06-26 | G | NZL | BEL | 1-3 | 0.7 | 2.6 | BEL |
| 67 | 2026-06-27 | L | HRV | GHA | 4-1 | 4.0 | 1.4 | HRV |
| 68 | 2026-06-27 | L | PAN | GBR | 2-3 | 1.5 | 2.6 | GBR |
| 69 | 2026-06-27 | K | COL | PRT | 2-2 | 1.9 | 2.2 | PRT |
| 70 | 2026-06-27 | K | COD | UZB | 3-2 | 2.7 | 2.1 | COD |
| 71 | 2026-06-27 | J | DZA | AUT | 3-1 | 2.6 | 1.5 | DZA |
| 72 | 2026-06-27 | J | JOR | ARG | 1-2 | 0.9 | 2.4 | ARG |

---

## The Model

The model is a **50/50 blend** between a normalised FIFA points score and a normalised economic metric score. Depending on the relative strength of the scores, an expected goals number is produced to predict the result of the game.

### Economic Formula

After extensive calibration, the economic model uses six macroeconomic indicators — population, real GDP growth, inflation, unemployment, policy rates, and government debt-to-GDP ratios:

```
Econ Score = (log₁₀(Pop) − 6)^1.2 × (1 + GDP/8) × 1/(1 + Infl/8) × (1 − Unemp) × 1/(1 + Rate/20) × 1/(0.8 + Debt/GDP ÷ 5)
```

### Rationale for Each Metric

**Population** is the bedrock of the model. Football is a numbers game: the more people you have, the more likely it is that a few of them can do something with a ball. We use a log scale because going from 5 million to 50 million matters enormously, but going from 500 million to 5 billion does not help you find a better left back. For very small nations (population under 1 million), the population term is clamped to zero — you cannot conjure a starting XI from thin air.

**GDP growth** captures momentum. A growing economy tends to mean investment in infrastructure, and with that comes football academies. A country expanding at 8% annually is building pitches; a country contracting at 8% is closing them.

**Inflation** is the instability penalty. When the price of a matchday pie is doubling every year, it is hard to maintain the kind of institutional stability that produces world-class players. The formula divides by (1 + Infl/8), so 8% inflation halves the contribution; 40% inflation reduces it to a sixth.

**Unemployment** is a proxy for development. Lower unemployment signals a functioning economy, disposable income for grassroots football, and parents who can afford to let their children train rather than study for work. This term enters as (1 − Unemp), a direct subtraction from 1.0.

**The policy rate** is a good signal for macroeconomic credibility. Countries with rates below 5% tend to be places where institutions work — central banks have earned the trust to keep money cheap, and that same institutional quality tends to produce competent football federations. The formula divides by (1 + Rate/20), so a 20% rate cuts the contribution by two-thirds.

**Government debt to GDP** is deliberately the weakest factor. Japan, for example, at 255%, would otherwise be pushed too far down the rankings. We penalise heavy debt gently — like a yellow card rather than a red. The term is 1/(0.8 + Debt/5), so Japan's debt reduces its multiplier to 0.76 rather than something catastrophic.

### The FIFA Anchor

Finally, we blend the economic score 50/50 with the **FIFA World Rankings** (the official ones from 1 April 2026) to stop the model producing results that are funny for thirty seconds and then become a credibility problem. Argentina finishing behind Curaçao on pure economics is entertaining, but the rankings anchor reminds us that Scaloni's squad is probably still quite good despite the peso.

### Expected Goals & Randomness

Each team's blended score (0–1 range) is mapped to expected goals via a linear scale:

```
xG = blended_score × 4
```

A small Gaussian noise term (σ = 0.3) is added to account for the no-shortage-of-variance in sporting events, with results clamped between 0 and 4 goals. The final score prediction is obtained by rounding each team's noisy xG to the nearest integer.

---

## Data Sources

| Metric | Source | Access |
|--------|--------|--------|
| FIFA Ranking Points | FIFA/Coca-Cola Men's World Ranking, 1 April 2026 | Public |
| GDP Growth, Inflation, Unemployment, Debt/GDP, Population | IMF World Economic Outlook, April 2026 | Free API |
| Central Bank Policy Rates | Bank for International Settlements (BIS), CBPOL dataset | Free API |

All data is fetched live at runtime. No API keys required.

---

## Running the Model

```bash
# Install
pip install -e ".[dev]"

# Generate predictions (live data from IMF + BIS)
python -m src.cli --seed 42 --output-dir ./output

# Or with deterministic mock data for testing
python -m src.cli --seed 42 --no-fetch --output-dir ./output

# Run tests
python -m pytest tests/ -v
```

Outputs: `output/world_cup_predictions.csv` and `output/world_cup_predictions.xlsx`

---

## Betting Research System (Phase 1 MVP)

The betting engine converts the macro-football model's expected goals (xG) into calibrated match-outcome probabilities and compares them against Bet365 odds to identify positive expected value (EV) betting opportunities.

### Markets Supported

| Market | Description |
|--------|-------------|
| 1X2 | Home win / Draw / Away win |
| Over/Under 2.5 | Total goals over or under 2.5 |
| BTTS | Both teams to score (yes/no) |

### How It Works

1. **Clean xG extraction** — the prediction model now outputs noise-free xG values alongside the standard noisy predictions
2. **Poisson probability engine** — converts (xG_home, xG_away) into probability distributions using a Poisson goal grid (max_goals=10)
3. **Odds ingestion** — reads Bet365 odds from a manually-exported CSV (no scraping required)
4. **Overround normalization** — removes bookmaker margin via proportional method to compute fair implied probabilities
5. **EV calculation** — ranks bets by expected value: `EV = p_model × odds − 1`
6. **Fractional Kelly staking** — recommends stake sizes using quarter-Kelly with a 5% bankroll hard cap
7. **Paper bet ledger** — append-only CSV tracking all candidates with 17-column audit trail

### Running the Betting CLI

```bash
# Help
python -m src.betting.cli --help

# Full pipeline with sample odds (mock data for offline testing)
python -m src.betting.cli \
    --odds tests/fixtures/sample_odds.csv \
    --no-fetch \
    --bankroll 1000 \
    --output-dir ./output/betting

# With custom EV thresholds
python -m src.betting.cli \
    --odds odds.csv \
    --no-fetch \
    --min-ev 0.05 \
    --min-odds 1.50 \
    --max-odds 3.50 \
    --kelly-fraction 0.25
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--odds PATH` | (required) | Path to Bet365 odds CSV |
| `--bankroll FLOAT` | 1000.0 | Starting bankroll |
| `--no-fetch` | false | Use mock data (offline mode) |
| `--output-dir PATH` | ./output/betting | Output directory for ledger |
| `--min-ev FLOAT` | 0.03 | Minimum EV threshold (3% for paper) |
| `--min-odds FLOAT` | 1.50 | Minimum decimal odds |
| `--max-odds FLOAT` | 3.50 | Maximum decimal odds |
| `--kelly-fraction FLOAT` | 0.25 | Fraction of full Kelly |
| `--max-stake-pct FLOAT` | 0.05 | Max stake as % of bankroll |

### Odds CSV Format

Create a CSV from Bet365's website (manual export — NO scraping):

```
timestamp,event_id,kickoff,home,away,book,market,selection,line,decimal_odds
2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Spain,,1.22
2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Draw,,5.50
2026-06-15T12:00:00,WC2026-13,2026-06-15T18:00:00,Spain,Cabo Verde,bet365,1X2,Cabo Verde,,15.00
```

### Example Output

```
=== BETTING CANDIDATES (ranked by EV) ===

Match                     Selection        Odds     Model%   EV       Stake   
---------------------------------------------------------------------------
IRN vs NZL                IRN              1.90     60.5%    15.0%    $41.60
SAU vs URY                URY              2.05     55.4%    13.6%    $32.49

Total: 2 bets | Total stake: $74.09 | Bankroll: $1000.00
```

### Architecture

```
src/betting/
├── __init__.py
├── probabilities.py    ← Poisson PMF, 1X2, Totals, BTTS
├── odds.py             ← CSV parser, overround removal
├── validation.py       ← Team name resolution, odds validation
├── selector.py         ← EV calculator, Kelly staking
├── ledger.py           ← Append-only CSV ledger
└── cli.py              ← Full pipeline CLI
```

### Testing

```bash
# All tests (existing + betting)
python -m pytest tests/ -v          # 143 tests

# Betting tests only
python -m pytest tests/betting/ -v  # 52 tests

# Regression gate (existing tests unchanged)
python -m pytest tests/ -v --ignore=tests/betting/  # 91 tests
```

### Phase 2 (Planned)

- Historical backtesting (WC 2010-2022)
- Probability calibration (Brier score, reliability curves)
- Closing Line Value (CLV) tracking
- Research validator (injuries, lineups, weather, rest days)
- Elo/SPI/squad-value feature engineering
- Dixon-Coles low-score correlation adjustment
- DNB & Asian handicap markets
- Web dashboard

---

## Disclaimer

This model is a quantitative experiment blending macroeconomics with sports forecasting. It is not investment advice. Past performance (or lack thereof) is not a guide to future results. The value of your World Cup bracket may go down as well as up.

*Model architecture inspired by the macro-to-football framework described at [Bond Vigilantes](https://bondvigilantes.com/blog/2026/06/the-bond-vigilantes-world-cup-model/).*
