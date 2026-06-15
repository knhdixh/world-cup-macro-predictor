"""Expected value calculation and bet selection engine."""

from __future__ import annotations

from typing import Any


def expected_value(p_model: float, decimal_odds: float) -> float:
    """Compute expected value for a single bet."""
    return p_model * decimal_odds - 1.0


def kelly_fraction(
    p_model: float,
    decimal_odds: float,
    fraction: float = 0.25,
) -> float:
    """Compute the Kelly Criterion stake fraction.

    Full Kelly formula: f* = (p * odds - 1) / (odds - 1)
    Fractional Kelly: stake = fraction * f*

    Returns 0.0 if edge <= 0 or odds <= 1.

    Parameters
    ----------
    p_model : float
        Model probability of the outcome (0 to 1).
    decimal_odds : float
        Bookmaker decimal odds (> 1.0).
    fraction : float, default 0.25
        Fraction of full Kelly to use (0.25 = quarter-Kelly).

    Returns
    -------
    float
        Fraction of bankroll to stake. 0.0 means no bet.
    """
    if decimal_odds <= 1.0 or p_model <= 0.0:
        return 0.0
    ev = p_model * decimal_odds - 1.0
    if ev <= 0.0:
        return 0.0
    full_kelly = ev / (decimal_odds - 1.0)
    return max(0.0, fraction * full_kelly)


def recommend_stake(
    bankroll: float,
    p_model: float,
    decimal_odds: float,
    fraction: float = 0.25,
    max_stake_pct: float = 0.05,
) -> dict[str, float]:
    """Recommend a stake amount with hard caps.

    Computes fractional Kelly stake, then caps at max_stake_pct of bankroll.

    Parameters
    ----------
    bankroll : float
        Current bankroll.
    p_model : float
        Model probability of the outcome.
    decimal_odds : float
        Bookmaker decimal odds.
    fraction : float, default 0.25
        Fraction of full Kelly.
    max_stake_pct : float, default 0.05
        Maximum stake as fraction of bankroll (5% hard cap).

    Returns
    -------
    dict
        {"kelly": full_kelly_fraction, "stake": capped_stake, "pct_bankroll": stake/bankroll}
    """
    kelly = kelly_fraction(p_model, decimal_odds, fraction=1.0)  # full Kelly
    raw_stake = bankroll * kelly_fraction(p_model, decimal_odds, fraction)
    capped_stake = min(raw_stake, bankroll * max_stake_pct)
    pct = capped_stake / bankroll if bankroll > 0 else 0.0
    return {"kelly": round(kelly, 6), "stake": round(capped_stake, 2), "pct_bankroll": round(pct, 6)}


def edge(p_model: float, implied_prob: float) -> float:
    """Compute edge = model probability minus market implied probability."""
    return p_model - implied_prob


def is_candidate(
    ev: float,
    decimal_odds: float,
    min_ev: float = 0.03,
    min_odds: float = 1.50,
    max_odds: float = 3.50,
) -> bool:
    """Check if a bet meets minimum EV and odds criteria."""
    return ev >= min_ev and min_odds <= decimal_odds <= max_odds


def select_bets(
    predictions: list[dict[str, Any]],
    odds_data: list[dict[str, Any]],
    min_ev: float = 0.03,
    min_odds: float = 1.50,
    max_odds: float = 3.50,
) -> list[dict[str, Any]]:
    """Rank bet candidates by expected value.

    This Phase 1 selector works on pre-computed prediction rows and matches
    odds by event_id and selection names (including resolved team aliases).
    """

    from src.betting.odds import remove_overround
    from src.betting.probabilities import match_outcome_probs
    from src.betting.validation import resolve_team_name

    candidates: list[dict[str, Any]] = []

    event_odds: dict[str, dict[str, float]] = {}
    for row in odds_data:
        event_id = str(row["event_id"])
        event_odds.setdefault(event_id, {})[str(row["selection"])] = float(row["decimal_odds"])

    def selection_aliases(selection: str, team_name: str = "") -> set[str]:
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

    for pred in predictions:
        event_id = str(pred.get("event_id", ""))
        team_a = str(pred.get("team_a", ""))
        team_b = str(pred.get("team_b", ""))
        clean_xg_h = float(pred.get("team_a_clean_xg", 0.0))
        clean_xg_a = float(pred.get("team_b_clean_xg", 0.0))

        if event_id not in event_odds:
            continue

        probs = match_outcome_probs(clean_xg_h, clean_xg_a)
        selections = [
            (team_a, probs["home"]),
            ("Draw", probs["draw"]),
            (team_b, probs["away"]),
        ]

        market_odds = event_odds[event_id]
        no_vig_probs: dict[str, float] = {}
        if len(market_odds) >= 2:
            try:
                no_vig_probs = remove_overround(market_odds)
            except (ValueError, ZeroDivisionError):
                no_vig_probs = {}

        for selection_name, model_prob in selections:
            matched_odds = None
            matched_key = None
            if selection_name == "Draw":
                keys = ["Draw", "draw"]
            else:
                keys = list(selection_aliases(selection_name, selection_name))

            for key in keys:
                if key in market_odds:
                    matched_odds = market_odds[key]
                    matched_key = key
                    break

            if matched_odds is None:
                continue

            ev_val = expected_value(model_prob, matched_odds)
            if not is_candidate(ev_val, matched_odds, min_ev, min_odds, max_odds):
                continue

            implied_prob = 1.0 / matched_odds if matched_odds > 0 else 0.0
            if no_vig_probs:
                for key in ([matched_key] if matched_key else []) + (["Draw", "draw"] if selection_name == "Draw" else list(selection_aliases(selection_name, selection_name))):
                    if key in no_vig_probs:
                        implied_prob = no_vig_probs[key]
                        break

            candidates.append(
                {
                    "event_id": event_id,
                    "team_a": team_a,
                    "team_b": team_b,
                    "market": "1X2",
                    "selection": selection_name,
                    "model_prob": round(model_prob, 6),
                    "implied_prob": round(implied_prob, 6),
                    "decimal_odds": matched_odds,
                    "edge": round(edge(model_prob, implied_prob), 6),
                    "ev": round(ev_val, 6),
                }
            )

    candidates.sort(key=lambda candidate: candidate["ev"], reverse=True)
    return candidates
