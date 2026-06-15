2026-06-15: Added clean xG outputs to predict_match() before Gaussian noise and covered the new fields with extension tests.
2026-06-15: Betting validation should derive aliases from COUNTRY_MAP and accept common variants like Ivory Coast, South Korea, Iran, Türkiye, Curacao, Cabo Verde, and DR Congo.
2026-06-15: Added Poisson xG helpers with a low-lambda floor at 1e-6; truncated distributions for lam=4.0 stay within the 0.001 tail threshold at max_goals=10.
2026-06-15: Added CSV odds ingestion with utf-8-sig handling, multi-error validation, and float conversion for decimal_odds.
2026-06-15: Added proportional overround removal and market grouping helpers; no-vig probabilities are normalized per event/market and should sum to 1.0 within 0.0001.
2026-06-15: Added totals_probs() for 2.5 goal lines using summed Poisson xG and btts_probs() using independent scoring probabilities; BTTS currently assumes no Dixon-Coles correlation adjustment.
2026-06-15: Added EV selector helpers (expected_value, edge, is_candidate) and a Phase 1 1X2 selector that matches odds by event_id and team aliases, filters by EV/odds range, and sorts candidates by EV.
2026-06-15: Added fractional Kelly staking helpers (kelly_fraction, recommend_stake) using quarter-Kelly by default and a hard 5% bankroll cap; odds <= 1 or non-positive EV return 0.0.
2026-06-15: Added append-only paper bet ledger helpers with CSV DictWriter header creation, sequential bankroll tracking, and readback of candidate rows; ledger is schema-locked to 17 columns.
2026-06-15: Created src/betting/cli.py — betting CLI entry point orchestrating the full pipeline (predictions → odds → EV selection → Kelly staking → ledger). Uses seed=None for deterministic clean_xg (no noise). Default thresholds: min_ev=0.03, min_odds=1.50, max_odds=3.50, quarter-Kelly at 25%, 5% max stake cap.
2026-06-15: Added reverse ISO3→FIFA name mappings to validation.py TEAM_ALIASES so select_bets can match predictions (ISO3) against odds CSV selections (FIFA display names). Without this, selection_aliases("BEL", "BEL") only yielded {"BEL"} which never matched "Belgium" in the odds file.
2026-06-15: Created tests/betting/test_cli.py with 5 test cases across 3 groups: --help (exit 0 + option coverage), missing --odds (exit 2), E2E with mock data (produces ledger CSV with ≥1 bet row), and high min_ev filter (exit 0 with empty ledger).
