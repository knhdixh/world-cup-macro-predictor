"""Command-line interface for the betting pipeline.

Orchestrates the full betting pipeline:
1. Load/run prediction pipeline (using existing src modules)
2. Load odds from CSV
3. Select positive-EV bets
4. Apply Kelly staking
5. Write results to ledger
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

from src.aggregate import build_dataset, normalize_scores
from src.country_map import COUNTRY_MAP
from src.fifa_data import FIFA_DATA
from src.predict import predict_all_upcoming
from src.schedule import get_upcoming_matches

from src.betting.ledger import init_ledger, log_bets
from src.betting.odds import CsvOddsProvider, validate_odds_csv
from src.betting.selector import recommend_stake, select_bets

logger = logging.getLogger(__name__)

__all__ = ["build_betting_parser", "main"]

DEFAULT_BANKROLL = 1000.0
DEFAULT_OUTPUT_DIR = "./output/betting"
DEFAULT_MIN_EV = 0.03
DEFAULT_MIN_ODDS = 1.50
DEFAULT_MAX_ODDS = 3.50
DEFAULT_KELLY_FRACTION = 0.25
DEFAULT_MAX_STAKE_PCT = 0.05


def build_betting_parser() -> argparse.ArgumentParser:
    """Build and return the betting CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m src.betting.cli",
        description="World Cup betting research pipeline. "
                    "Matches model probabilities against bookmaker odds "
                    "and outputs positive-EV bet candidates.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--odds",
        type=str,
        required=True,
        help="Path to odds CSV file (Bet365 format)",
    )
    parser.add_argument(
        "--bankroll",
        type=float,
        default=DEFAULT_BANKROLL,
        help="Starting bankroll for stake sizing",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        default=False,
        help="Skip IMF/BIS HTTP calls and use mock data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(DEFAULT_OUTPUT_DIR),
        help="Directory for output files (ledger CSV)",
    )
    parser.add_argument(
        "--min-ev",
        type=float,
        default=DEFAULT_MIN_EV,
        help="Minimum EV threshold (0.03 = 3%%). Raise to 0.05 for live betting.",
    )
    parser.add_argument(
        "--min-odds",
        type=float,
        default=DEFAULT_MIN_ODDS,
        help="Minimum decimal odds",
    )
    parser.add_argument(
        "--max-odds",
        type=float,
        default=DEFAULT_MAX_ODDS,
        help="Maximum decimal odds",
    )
    parser.add_argument(
        "--kelly-fraction",
        type=float,
        default=DEFAULT_KELLY_FRACTION,
        help="Fraction of full Kelly to use (0.25 = quarter-Kelly)",
    )
    parser.add_argument(
        "--max-stake-pct",
        type=float,
        default=DEFAULT_MAX_STAKE_PCT,
        help="Maximum stake as fraction of bankroll (0.05 = 5%% hard cap)",
    )
    return parser


def _convert_match_to_iso3(match: dict[str, Any]) -> dict[str, Any] | None:
    """Map FIFA team names to ISO3 — same pattern as src/cli.py."""
    from src.country_map import get_iso3

    try:
        return {
            **match,
            "team_a": get_iso3(match["team_a"]),
            "team_b": get_iso3(match["team_b"]),
        }
    except KeyError as exc:
        logger.warning(
            "Skipping match #%s — unresolved team name: %s",
            match.get("match_number"),
            exc,
        )
        return None


def _mock_data():
    """Reuse mock data from src.cli to avoid duplication."""
    from src.cli import _mock_data as _cli_mock_data

    return _cli_mock_data(COUNTRY_MAP)


def main(argv: list[str] | None = None) -> int:
    """Run the full betting pipeline. Returns the process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = build_betting_parser().parse_args(argv)

    # 1. Load dataset (mock or live)
    if args.no_fetch:
        logger.info("--no-fetch set; using internal mock data")
        imf_data, bis_rates = _mock_data()
    else:
        logger.error("Live data fetching not implemented in Phase 1. Use --no-fetch.")
        return 1

    dataset = build_dataset(imf_data, bis_rates, FIFA_DATA, COUNTRY_MAP)
    dataset = normalize_scores(dataset)
    logger.info("Dataset built: %d rows", len(dataset))

    # 2. Get upcoming matches
    cutoff_date = date.today().isoformat()
    upcoming = get_upcoming_matches(cutoff_date)
    resolved = [
        m for m in (_convert_match_to_iso3(m) for m in upcoming) if m is not None
    ]
    logger.info(
        "Upcoming matches: %d (after resolving %d)",
        len(resolved),
        len(upcoming),
    )

    # 3. Predict matches
    # seed=None → no noise applied to xG; betting probabilities use clean_xg
    # which are purely deterministic from blended scores.
    predictions = predict_all_upcoming(resolved, dataset, seed=None)
    logger.info("Generated %d predictions", len(predictions))

    # 4. Inject event_ids from schedule into predictions
    for pred, match in zip(predictions, resolved):
        if "match_number" in match:
            pred["event_id"] = f"WC2026-{match['match_number']}"
        else:
            pred["event_id"] = ""

    # 5. Validate and load odds
    odds_path = args.odds
    try:
        validate_odds_csv(odds_path)
    except ValueError as e:
        logger.error("Odds CSV validation failed:\n%s", e)
        return 1

    provider = CsvOddsProvider(odds_path)
    odds_data = provider.fetch_odds()
    logger.info("Loaded %d odds rows from %s", len(odds_data), odds_path)

    # 6. Select EV bets
    candidates = select_bets(
        predictions,
        odds_data,
        min_ev=args.min_ev,
        min_odds=args.min_odds,
        max_odds=args.max_odds,
    )
    logger.info("Found %d betting candidates", len(candidates))

    # 7. Apply Kelly staking to each candidate
    bankroll = args.bankroll
    enriched = []
    for c in candidates:
        stake_info = recommend_stake(
            bankroll,
            c["model_prob"],
            c["decimal_odds"],
            fraction=args.kelly_fraction,
            max_stake_pct=args.max_stake_pct,
        )
        c["stake"] = stake_info["stake"]
        c["kelly"] = stake_info["kelly"]
        enriched.append(c)

    # 8. Print ranked candidates
    if enriched:
        print("\n=== BETTING CANDIDATES (ranked by EV) ===\n")
        print(
            f"{'Match':<25} {'Selection':<16} {'Odds':<8} {'Model%':<8} "
            f"{'EV':<8} {'Stake':<8}"
        )
        print("-" * 75)
        for c in enriched:
            match_label = f"{c['team_a']} vs {c['team_b']}"
            print(
                f"{match_label:<25} {c['selection']:<16} {c['decimal_odds']:<8.2f} "
                f"{c['model_prob']*100:<7.1f}% {c['ev']*100:<6.1f}% ${c['stake']:<5.2f}"
            )
        total_stake = sum(c["stake"] for c in enriched)
        print(
            f"\nTotal: {len(enriched)} bets | Total stake: ${total_stake:.2f} "
            f"| Bankroll: ${bankroll:.2f}"
        )
    else:
        print("\nNo betting candidates found with current criteria.")
        print(f"  min_ev={args.min_ev}, odds=[{args.min_odds}, {args.max_odds}]")

    # 9. Write to ledger
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = output_dir / "paper_bet_ledger.csv"
    init_ledger(ledger_path)
    remaining = log_bets(ledger_path, enriched, bankroll)
    logger.info(
        "Ledger written to %s (remaining bankroll: $%.2f)",
        ledger_path,
        remaining,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
