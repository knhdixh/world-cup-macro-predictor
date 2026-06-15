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
from src.betting.markets import asian_handicap_probs, dnb_probs
from src.betting.odds import validate_odds_csv
from src.betting.providers import OddsProviderRegistry
from src.betting.probabilities import btts_probs, match_outcome_probs, totals_probs
from src.betting.research import ResearchValidator
from src.betting.selector import recommend_stake
from src.betting.validation import resolve_team_name

logger = logging.getLogger(__name__)

__all__ = ["build_betting_parser", "main"]

DEFAULT_BANKROLL = 1000.0
DEFAULT_OUTPUT_DIR = "./output/betting"
DEFAULT_MIN_EV = 0.03
DEFAULT_MIN_ODDS = 1.50
DEFAULT_MAX_ODDS = 3.50
DEFAULT_KELLY_FRACTION = 0.25
DEFAULT_MAX_STAKE_PCT = 0.05
MARKET_CHOICES = ("1X2", "DNB", "AH-0.5", "BTTS", "O2.5")
ODDS_METHOD_CHOICES = ("csv", "api", "auto")


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
        default=None,
        help="Path to odds CSV file (Bet365 format; required for predict)",
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
    parser.add_argument(
        "--market",
        choices=MARKET_CHOICES,
        default="1X2",
        help="Betting market to evaluate",
    )
    parser.add_argument(
        "--odds-method",
        choices=ODDS_METHOD_CHOICES,
        default="csv",
        help="Odds source method",
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-command")
    parser.set_defaults(command="predict")

    bt_parser = subparsers.add_parser("backtest", help="Run historical backtest")
    bt_parser.add_argument("--bankroll", type=float, default=1000.0)
    bt_parser.add_argument("--min-ev", type=float, default=0.03)
    bt_parser.add_argument("--output", type=str, default=None, help="Save report to file")

    cal_parser = subparsers.add_parser("calibrate", help="Run calibration analysis")
    cal_parser.add_argument("--output", type=str, default=None)

    res_parser = subparsers.add_parser("research", help="Run research validator")
    res_parser.add_argument("--check", type=str, default=None, help="Team ISO3 to check")
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


def _api_market_key(market: str) -> str:
    if market in {"1X2", "DNB"}:
        return "h2h"
    if market == "AH-0.5":
        return "spreads"
    if market == "O2.5":
        return "totals"
    return "btts"


def _special_market_probabilities(market: str, xg_home: float, xg_away: float) -> dict[str, float]:
    if market == "DNB":
        return dnb_probs(xg_home, xg_away)
    if market == "AH-0.5":
        return asian_handicap_probs(xg_home, xg_away, line=-0.5)
    if market == "BTTS":
        return btts_probs(xg_home, xg_away)
    if market == "O2.5":
        return totals_probs(xg_home, xg_away)
    return match_outcome_probs(xg_home, xg_away)


def _selection_aliases(selection: str, team_name: str = "") -> set[str]:
    aliases = {selection}
    if selection != "Draw":
        aliases.add(team_name)
        if team_name:
            try:
                aliases.add(resolve_team_name(team_name))
            except ValueError:
                pass
        try:
            aliases.add(resolve_team_name(selection))
        except ValueError:
            pass
    return {alias for alias in aliases if alias}


def _special_market_selections(
    market: str,
    team_a: str,
    team_b: str,
    probs: dict[str, float],
) -> list[tuple[str, float]]:
    if market == "DNB" or market == "AH-0.5":
        return [(team_a, probs["home"]), (team_b, probs["away"])]
    if market == "BTTS":
        return [("Yes", probs["yes"]), ("No", probs["no"])]
    if market == "O2.5":
        return [("Over", probs["over"]), ("Under", probs["under"])]
    return [(team_a, probs["home"]), ("Draw", probs["draw"]), (team_b, probs["away"])]


def _special_market_candidates(
    predictions: list[dict[str, Any]],
    odds_data: list[dict[str, Any]],
    market: str,
    odds_markets: set[str],
    min_ev: float,
    min_odds: float,
    max_odds: float,
) -> list[dict[str, Any]]:
    event_odds: dict[str, dict[str, float]] = {}
    for row in odds_data:
        if str(row.get("market", "")) not in odds_markets:
            continue
        event_id = str(row["event_id"])
        event_odds.setdefault(event_id, {})[str(row["selection"])] = float(row["decimal_odds"])

    candidates: list[dict[str, Any]] = []
    for pred in predictions:
        event_id = str(pred.get("event_id", ""))
        if event_id not in event_odds:
            continue

        team_a = str(pred.get("team_a", ""))
        team_b = str(pred.get("team_b", ""))
        probs = _special_market_probabilities(
            market,
            float(pred.get("team_a_clean_xg", 0.0)),
            float(pred.get("team_b_clean_xg", 0.0)),
        )
        selections = _special_market_selections(market, team_a, team_b, probs)
        market_odds = event_odds[event_id]

        for selection_name, model_prob in selections:
            matched_odds = None
            if selection_name == "Draw":
                keys = ["Draw", "draw"]
            elif market == "BTTS":
                keys = [selection_name, f"BTTS {selection_name}", f"Both teams to score {selection_name}"]
            elif market == "O2.5":
                keys = [selection_name, f"{selection_name} 2.5", f"{selection_name} 2.5 Goals"]
            else:
                keys = list(_selection_aliases(selection_name, selection_name))

            for key in keys:
                if key in market_odds:
                    matched_odds = market_odds[key]
                    break

            if matched_odds is None:
                continue

            ev_val = model_prob * matched_odds - 1.0
            if not (ev_val >= min_ev and min_odds <= matched_odds <= max_odds):
                continue

            candidate = {
                "event_id": event_id,
                "team_a": team_a,
                "team_b": team_b,
                "market": market,
                "selection": selection_name,
                "model_prob": round(model_prob, 6),
                "decimal_odds": matched_odds,
                "ev": round(ev_val, 6),
                "match_date": pred.get("match_date", ""),
                "tournament_stage": pred.get("tournament_stage", "group"),
            }
            if market in {"1X2", "DNB", "AH-0.5"} and selection_name != "Draw":
                candidate["team_iso3"] = team_a if selection_name == team_a else team_b
            candidates.append(candidate)

    candidates.sort(key=lambda candidate: candidate["ev"], reverse=True)
    return candidates


def _apply_research_veto(candidates: list[dict[str, Any]], validator: ResearchValidator) -> list[dict[str, Any]]:
    vetted: list[dict[str, Any]] = []
    for candidate in candidates:
        team_iso3 = str(candidate.get("team_iso3", "")).strip()
        if not team_iso3:
            vetted.append(candidate)
            continue

        approved, reason = validator.veto_bet(candidate)
        if approved:
            vetted.append(candidate)
        else:
            logger.info("Skipping %s %s: %s", candidate.get("event_id", ""), candidate.get("selection", ""), reason)
    return vetted


def main(argv: list[str] | None = None) -> int:
    """Run the full betting pipeline. Returns the process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = build_betting_parser()
    args = parser.parse_args(argv)

    if args.command == "backtest":
        from src.betting.backtest import generate_backtest_report, run_backtest

        results = run_backtest(bankroll=args.bankroll, min_ev=args.min_ev)
        report = generate_backtest_report(results)
        print(report)
        if args.output:
            Path(args.output).write_text(report)
        return 0

    if args.command == "calibrate":
        from src.betting.backtest import run_backtest
        from src.betting.calibration import brier_score, log_loss_score, reliability_curve

        results = run_backtest()
        bets = results["results"]

        probs = [b["model_prob"] for b in bets if "model_prob" in b]
        outcomes = [1 if b.get("won") else 0 for b in bets if "won" in b]

        if probs:
            lines = [f"Brier Score: {brier_score(probs, outcomes):.4f}", f"Log Loss: {log_loss_score(probs, outcomes):.4f}"]
            curve = reliability_curve(probs, outcomes)
            lines.append(f"Calibration bins: {len(curve['bin_centers'])}")
            for i in range(len(curve["bin_centers"])):
                lines.append(
                    f"  {curve['bin_centers'][i]*100:.0f}%: "
                    f"predicted={curve['mean_predicted'][i]:.3f} "
                    f"actual={curve['mean_actual'][i]:.3f} n={curve['counts'][i]}"
                )
            report = "\n".join(lines)
            print(report)
            if args.output:
                Path(args.output).write_text(report)
        return 0

    if args.command == "research":
        validator = ResearchValidator()
        try:
            validator.load_injuries()
        except FileNotFoundError as exc:
            logger.error(str(exc))
            return 1

        if args.check:
            injuries = validator.check_injuries(args.check)
            print(f"Injuries for {args.check}: {injuries if injuries else 'None reported'}")
        else:
            print("Usage: python -m src.betting.cli research --check <team_iso3>")
        return 0

    if not args.odds:
        parser.error("--odds is required for the predict command")

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
        pred["match_date"] = str(match.get("date", ""))
        pred["tournament_stage"] = "group"
        pred["matchday"] = match.get("matchday")

    # 5. Validate and load odds
    try:
        if args.odds_method == "csv":
            validate_odds_csv(args.odds)
    except ValueError as e:
        logger.error("Odds CSV validation failed:\n%s", e)
        return 1

    registry = OddsProviderRegistry(csv_path=args.odds)
    odds_data = registry.get_odds(method=args.odds_method, markets=_api_market_key(args.market))
    logger.info("Loaded %d odds rows via %s from %s", len(odds_data), args.odds_method, args.odds)

    # 6. Select EV bets
    candidates = _special_market_candidates(
        predictions,
        odds_data,
        args.market,
        {args.market, _api_market_key(args.market)} if args.odds_method == "auto" else ({_api_market_key(args.market)} if args.odds_method == "api" else {args.market}),
        args.min_ev,
        args.min_odds,
        args.max_odds,
    )
    logger.info("Found %d betting candidates", len(candidates))

    validator = ResearchValidator()
    try:
        validator.load_injuries()
        candidates = _apply_research_veto(candidates, validator)
    except FileNotFoundError:
        logger.warning("Research validator data missing; skipping veto checks")

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
