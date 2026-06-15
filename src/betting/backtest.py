"""Backtesting engine — replay Phase 1 model on historical data."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from src.betting.historical import HistoricalDB
from src.betting.probabilities import match_outcome_probs
from src.betting.selector import expected_value, is_candidate, kelly_fraction
from src.betting.analysis import odds_bucket_roi, market_roi_matrix


def run_backtest(
    db: HistoricalDB | None = None,
    bankroll: float = 1000.0,
    min_ev: float = 0.03,
    min_odds: float = 1.50,
    max_odds: float = 3.50,
    kelly_frac: float = 0.25,
) -> dict[str, Any]:
    """Run a full backtest of the Phase 1 betting model on historical data.

    For each historical match:
    1. Compute xG from FIFA ranking data (proxy for blended score)
    2. Convert to 1X2 probabilities via Poisson
    3. Compare against historical odds
    4. If EV positive and odds in range, log a bet
    5. Track actual result (from historical data)

    Parameters
    ----------
    db : HistoricalDB | None
        Database instance. Fresh instance created if None.
    bankroll : float
        Starting bankroll.
    min_ev : float
        Minimum expected value threshold.
    min_odds : float
        Minimum decimal odds filter.
    max_odds : float
        Maximum decimal odds filter.
    kelly_frac : float
        Fraction of full Kelly to stake.

    Returns
    -------
    dict with keys:
        "results": list of bet dicts
        "summary": overall metrics
        "by_tournament": per-tournament breakdown
        "by_odds_bucket": odds bucket analysis
        "by_market": market ROI matrix
    """
    _db = HistoricalDB() if db is None else db
    matches = _db.get_all_matches()

    # Group matches by tournament for per-tournament FIFA normalization
    tournaments: dict[int, list[dict[str, Any]]] = {}
    for m in matches:
        tournaments.setdefault(int(m["tournament"]), []).append(m)

    all_results: list[dict[str, Any]] = []
    balance = bankroll
    balance_history: list[float] = [bankroll]

    for tournament_year in sorted(tournaments):
        t_matches = tournaments[tournament_year]

        # Compute per-tournament min/max FIFA for normalization
        fifa_vals: set[float] = set()
        for m in t_matches:
            fifa_vals.add(float(m["team_a_fifa"]))
            fifa_vals.add(float(m["team_b_fifa"]))
        min_fifa = min(fifa_vals)
        max_fifa = max(fifa_vals)
        fifa_range = max_fifa - min_fifa if max_fifa != min_fifa else 1.0

        for m in t_matches:
            # Normalize FIFA points across all teams in the tournament.
            # This is the proxy for the blended score (no economic data).
            norm_home = (float(m["team_a_fifa"]) - min_fifa) / fifa_range
            norm_away = (float(m["team_b_fifa"]) - min_fifa) / fifa_range

            # xG = normalized_blended_score * 4
            xg_home = norm_home * 4.0
            xg_away = norm_away * 4.0

            bets = _simulate_match_outcome(
                team_a=str(m["team_a"]),
                team_b=str(m["team_b"]),
                tournament=tournament_year,
                match_number=int(m["match_number"]),
                date=str(m["date"]),
                xg_home=xg_home,
                xg_away=xg_away,
                odds_home=float(m["odds_home"]),
                odds_draw=float(m["odds_draw"]),
                odds_away=float(m["odds_away"]),
                actual_home_goals=int(m["team_a_goals"]),
                actual_away_goals=int(m["team_b_goals"]),
                bankroll=balance,
                min_ev=min_ev,
                min_odds=min_odds,
                max_odds=max_odds,
                kelly_frac=kelly_frac,
            )

            for bet in bets:
                balance += bet["profit"]
                balance_history.append(balance)

            all_results.extend(bets)

    # ---- Summary metrics ----
    total_bets = len(all_results)
    total_stake = sum(float(b["stake"]) for b in all_results)
    total_profit = sum(float(b["profit"]) for b in all_results)
    wins = sum(1 for b in all_results if b["won"])
    roi = total_profit / total_stake if total_stake else 0.0
    win_rate = wins / total_bets if total_bets else 0.0

    summary: dict[str, Any] = {
        "total_bets": total_bets,
        "total_stake": round(total_stake, 2),
        "total_profit": round(total_profit, 2),
        "roi": round(roi, 6),
        "win_rate": round(win_rate, 6),
        "max_drawdown": round(_max_drawdown(balance_history), 6),
        "final_bankroll": round(balance, 2),
        "starting_bankroll": bankroll,
    }

    # ---- Per-tournament breakdown ----
    by_tournament: dict[str, dict[str, Any]] = OrderedDict()
    for year in sorted(tournaments):
        year_results = [b for b in all_results if b["tournament"] == year]
        if not year_results:
            continue
        y_stake = sum(float(b["stake"]) for b in year_results)
        y_profit = sum(float(b["profit"]) for b in year_results)
        y_wins = sum(1 for b in year_results if b["won"])
        y_total = len(year_results)
        by_tournament[str(year)] = {
            "bets": y_total,
            "total_stake": round(y_stake, 2),
            "total_profit": round(y_profit, 2),
            "roi": round(y_profit / y_stake, 6) if y_stake else 0.0,
            "win_rate": round(y_wins / y_total, 6) if y_total else 0.0,
        }

    return {
        "results": all_results,
        "summary": summary,
        "by_tournament": dict(by_tournament),
        "by_odds_bucket": odds_bucket_roi(all_results),
        "by_market": market_roi_matrix(all_results),
    }


def _simulate_match_outcome(
    team_a: str,
    team_b: str,
    tournament: int,
    match_number: int,
    date: str,
    xg_home: float,
    xg_away: float,
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    actual_home_goals: int,
    actual_away_goals: int,
    bankroll: float,
    min_ev: float,
    min_odds: float,
    max_odds: float,
    kelly_frac: float,
) -> list[dict[str, Any]]:
    """Simulate betting on a single match.

    How xG is computed from FIFA (in ``run_backtest``):
    - FIFA points are min-max normalized across all teams in the tournament
      to a 0-1 score. This normalized value serves as the proxy for the
      blended score (since historical economic data is unavailable).
    - xG = normalized_fifa * 4

    For each of the three 1X2 selections (home / draw / away):
    - Compute model probability via Poisson goal distribution
    - Compute expected value (EV)
    - If EV and odds pass the filters, place a fractional Kelly bet
    - Determine profit based on actual match outcome

    Parameters
    ----------
    xg_home : float
        Expected goals for team_a (computed externally via tournament-wide
        FIFA normalization).
    xg_away : float
        Expected goals for team_b.

    Returns
    -------
    list[dict[str, Any]]
        One dict per qualifying bet selection.
    """
    probs = match_outcome_probs(xg_home, xg_away)
    match_label = f"{team_a} vs {team_b}"

    # Determine actual outcome from goal counts
    if actual_home_goals > actual_away_goals:
        actual_winner = "home"
    elif actual_home_goals == actual_away_goals:
        actual_winner = "draw"
    else:
        actual_winner = "away"

    selections: list[tuple[str, float, float]] = [
        (team_a, probs["home"], odds_home),
        ("Draw", probs["draw"], odds_draw),
        (team_b, probs["away"], odds_away),
    ]

    bets: list[dict[str, Any]] = []

    for selection_name, model_prob, decimal_odds in selections:
        if decimal_odds <= 0:
            continue

        ev_val = expected_value(model_prob, decimal_odds)

        if not is_candidate(ev_val, decimal_odds, min_ev, min_odds, max_odds):
            continue

        # Compute stake using fractional Kelly
        kelly_frac_val = kelly_fraction(model_prob, decimal_odds, kelly_frac)
        # Cap at 5% of bankroll (standard risk management)
        max_stake = bankroll * 0.05
        stake = min(bankroll * kelly_frac_val, max_stake)
        stake = max(stake, 0.0)

        if stake <= 0:
            continue

        # Determine if this selection won
        if selection_name == team_a:
            won = actual_winner == "home"
        elif selection_name == "Draw":
            won = actual_winner == "draw"
        else:  # team_b
            won = actual_winner == "away"

        profit = stake * (decimal_odds - 1.0) if won else -stake

        bets.append({
            "match": match_label,
            "tournament": tournament,
            "match_number": match_number,
            "date": date,
            "market": "1X2",
            "selection": selection_name,
            "decimal_odds": round(decimal_odds, 4),
            "model_prob": round(model_prob, 6),
            "ev": round(ev_val, 6),
            "stake": round(stake, 2),
            "profit": round(profit, 2),
            "won": won,
        })

    return bets


def generate_backtest_report(results: dict[str, Any]) -> str:
    """Generate a markdown-formatted backtest report.

    Sections:
    - Overall metrics (ROI, win rate, profit, max drawdown)
    - Per-tournament breakdown
    - By odds bucket
    - By market type

    Parameters
    ----------
    results : dict
        Output of ``run_backtest()``.

    Returns
    -------
    str
        Markdown report.
    """
    summary = results.get("summary", {})
    by_tournament = results.get("by_tournament", {})
    by_odds_bucket = results.get("by_odds_bucket", {})
    by_market = results.get("by_market", {})

    lines: list[str] = []
    lines.append("# Backtest Report\n")
    lines.append("## Overall Metrics\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| Starting Bankroll | ${summary.get('starting_bankroll', 0):.2f} |"
    )
    lines.append(
        f"| Final Bankroll | ${summary.get('final_bankroll', 0):.2f} |"
    )
    lines.append(f"| Total Bets | {summary.get('total_bets', 0)} |")
    lines.append(
        f"| Total Stake | ${summary.get('total_stake', 0):.2f} |"
    )
    lines.append(
        f"| Total Profit | ${summary.get('total_profit', 0):+.2f} |"
    )
    lines.append(f"| ROI | {summary.get('roi', 0) * 100:.2f}% |")
    lines.append(f"| Win Rate | {summary.get('win_rate', 0) * 100:.2f}% |")
    lines.append(
        f"| Max Drawdown | {summary.get('max_drawdown', 0) * 100:.2f}% |"
    )
    lines.append("")

    # ---- Per-tournament breakdown ----
    lines.append("## Per-Tournament Breakdown\n")
    lines.append("| Tournament | Bets | Stake | Profit | ROI | Win Rate |")
    lines.append("|------------|------|-------|--------|-----|----------|")
    for year, tdata in by_tournament.items():
        lines.append(
            f"| {year} | {tdata['bets']} | "
            f"${tdata['total_stake']:.2f} | "
            f"${tdata['total_profit']:+.2f} | "
            f"{tdata['roi'] * 100:.2f}% | "
            f"{tdata['win_rate'] * 100:.2f}% |"
        )
    lines.append("")

    # ---- By odds bucket ----
    lines.append("## By Odds Bucket\n")
    if by_odds_bucket:
        lines.append(
            "| Bucket | Bets | Stake | Profit | ROI | Win Rate |"
        )
        lines.append(
            "|--------|------|-------|--------|-----|----------|"
        )
        for bucket, bdata in by_odds_bucket.items():
            lines.append(
                f"| {bucket} | {int(bdata['bets'])} | "
                f"${bdata['total_stake']:.2f} | "
                f"${bdata['total_profit']:+.2f} | "
                f"{bdata['roi'] * 100:.2f}% | "
                f"{bdata['win_rate'] * 100:.2f}% |"
            )
    else:
        lines.append("_(No bets placed)_")
    lines.append("")

    # ---- By market type ----
    lines.append("## By Market Type\n")
    if by_market:
        lines.append("| Market | Bets | Stake | Profit | ROI |")
        lines.append("|--------|------|-------|--------|-----|")
        for market, mdata in by_market.items():
            lines.append(
                f"| {market} | {int(mdata['bets'])} | "
                f"${mdata['total_stake']:.2f} | "
                f"${mdata['total_profit']:+.2f} | "
                f"{mdata['roi'] * 100:.2f}% |"
            )
    else:
        lines.append("_(No bets placed)_")
    lines.append("")

    return "\n".join(lines)


def _max_drawdown(balances: list[float]) -> float:
    """Compute maximum drawdown from a list of account balances.

    Maximum drawdown is the largest peak-to-trough decline expressed as a
    fraction of the peak.  For example, a balance sequence of
    ``[1000, 950, 900, 980, 970]`` has a max drawdown of 10%:
    ``(1000 - 900) / 1000 = 0.10``.

    Parameters
    ----------
    balances : list[float]
        Account balance at each step (first entry is the starting bankroll).

    Returns
    -------
    float
        Maximum drawdown as a fraction (0.10 = 10%).  Returns 0.0 for
        sequences with fewer than 2 elements.
    """
    if len(balances) < 2:
        return 0.0

    peak = balances[0]
    max_dd = 0.0

    for balance in balances[1:]:
        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd

    return max_dd
