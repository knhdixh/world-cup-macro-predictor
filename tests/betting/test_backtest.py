"""Tests for src.betting.backtest — backtesting engine."""

from src.betting.backtest import run_backtest, _max_drawdown


def test_run_backtest_basic() -> None:
    """Run backtest on all historical data, verify return structure."""
    results = run_backtest(min_ev=0.05, min_odds=1.50, max_odds=3.50)

    assert "results" in results
    assert "summary" in results
    assert "by_tournament" in results
    assert "by_odds_bucket" in results
    assert "by_market" in results

    assert isinstance(results["results"], list)
    assert isinstance(results["summary"], dict)
    assert isinstance(results["by_tournament"], dict)

    summary = results["summary"]
    assert summary["total_bets"] >= 0
    assert summary["total_stake"] >= 0
    assert "roi" in summary
    assert "win_rate" in summary
    assert "max_drawdown" in summary
    assert "final_bankroll" in summary
    assert "starting_bankroll" in summary

    # Verify tournament keys exist (2010, 2014, 2018, 2022)
    for year in ("2010", "2014", "2018", "2022"):
        assert year in results["by_tournament"], (
            f"Missing tournament {year} in breakdown"
        )


def test_backtest_bet_outcome() -> None:
    """For ARG vs SAU (2022), verify the bet outcome is captured correctly.

    Argentina (FIFA 1250, odds_home=1.54) vs Saudi Arabia (FIFA 850).
    The model strongly favours Argentina, so it should place a home bet.
    Since SAU won 2-1, the bet should be recorded as lost.
    """
    results = run_backtest(min_ev=0.05, min_odds=1.50, max_odds=3.50)

    # Find bets on Argentina vs Saudi Arabia
    arg_sau_bets = [
        b
        for b in results["results"]
        if "ARG" in b["match"] and "SAU" in b["match"]
    ]
    assert len(arg_sau_bets) > 0, (
        "Expected at least one bet on ARG vs SAU"
    )

    # The model's strongest probability is on Argentina (home)
    # so the bet on ARG should exist and have lost (SAU won 2-1)
    arg_bets = [b for b in arg_sau_bets if b["selection"] == "ARG"]
    draw_bets = [b for b in arg_sau_bets if b["selection"] == "Draw"]

    # At minimum the ARG home bet should be present
    assert len(arg_bets) >= 1, (
        "Expected a bet on ARG (home) for the match"
    )

    # Verify the odds are correct for the home bet
    home_bet = arg_bets[0]
    assert home_bet["decimal_odds"] == 1.54, (
        f"Expected odds 1.54 for ARG home, got {home_bet['decimal_odds']}"
    )

    # ARG lost 1-2 → bet should be lost
    assert home_bet["won"] is False, (
        "ARG lost to SAU 1-2, so the home bet should be lost"
    )
    assert home_bet["profit"] < 0, (
        "Lost bet should have negative profit"
    )

    # Draw bet should also exist if EV was positive (unlikely at 4.21 odds
    # with low draw probability, but just check it doesn't crash)
    for b in draw_bets:
        assert b["won"] is False, (
            "Draw bet should also be lost (ARG 1-2 SAU)"
        )


def test_max_drawdown() -> None:
    """Max drawdown from known balance sequence.

    [1000, 950, 900, 980, 970]:
    - Peak = 1000, trough = 900 → dd = 100/1000 = 0.10 (10%)
    """
    balances = [1000.0, 950.0, 900.0, 980.0, 970.0]
    dd = _max_drawdown(balances)
    assert abs(dd - 0.10) < 0.01, (
        f"Expected max drawdown 0.10, got {dd}"
    )

    # Edge cases
    assert _max_drawdown([]) == 0.0, "Empty list → 0.0"
    assert _max_drawdown([100.0]) == 0.0, "Single element → 0.0"
    assert _max_drawdown([100.0, 110.0, 120.0]) == 0.0, (
        "Monotonic increase → 0.0"
    )

    # Monotonic decrease: [100, 80, 60, 40]
    # Peak = 100, trough = 40 → dd = 60/100 = 0.60
    dd2 = _max_drawdown([100.0, 80.0, 60.0, 40.0])
    assert abs(dd2 - 0.60) < 0.01, (
        f"Expected 0.60, got {dd2}"
    )

    # New peak after drawdown resets peak: [100, 50, 150, 120]
    # Peak = 150, trough = 120 → dd = 30/150 = 0.20
    # But also earlier peak = 100, trough = 50 → dd = 0.50
    # Max dd = 0.50
    dd3 = _max_drawdown([100.0, 50.0, 150.0, 120.0])
    assert abs(dd3 - 0.50) < 0.01, (
        f"Expected 0.50, got {dd3}"
    )
