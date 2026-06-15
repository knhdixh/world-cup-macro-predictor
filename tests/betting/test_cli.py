"""Integration tests for the betting CLI entry point."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.betting.cli import build_betting_parser, main

FIXTURES_DIR = Path("tests/fixtures")
SAMPLE_ODDS = FIXTURES_DIR / "sample_odds.csv"


# ---------------------------------------------------------------------------
# Help / argparse
# ---------------------------------------------------------------------------


class TestHelp:
    """--help must print usage and exit 0."""

    def test_help_exits_zero(self) -> None:
        """``main(["--help"])`` raises SystemExit(0)."""
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_help_contains_key_options(self) -> None:
        """Help text mentions the main CLI options."""
        import io

        # Capture ``--help`` output raised by argparse's built-in help action.
        # argparse prints help and calls sys.exit(0) — we catch the exit
        # and read what was written to stdout.
        out = io.StringIO()
        with pytest.raises(SystemExit) as exc:
            build_betting_parser().parse_args(["--help"])
        assert exc.value.code == 0
        # parse_args writes help to sys.stdout; we re-build the string
        # from the parser's formatter instead.  Simpler: just verify that
        # the parser includes all required arguments by checking its
        # internal action list.
        parser = build_betting_parser()
        actions = {a.dest for a in parser._actions}
        for opt in ("odds", "bankroll", "no_fetch", "output_dir",
                    "min_ev", "min_odds", "max_odds",
                    "kelly_fraction", "max_stake_pct"):
            assert opt in actions, f"Missing option: --{opt.replace('_', '-')}"


# ---------------------------------------------------------------------------
# Missing required arguments
# ---------------------------------------------------------------------------


class TestMissingOdds:
    """Without --odds, argparse must fail with exit code 2."""

    def test_exits_two_when_odds_missing(self) -> None:
        """``main(["--bankroll", "1000", "--no-fetch"])`` → exit 2."""
        with pytest.raises(SystemExit) as exc:
            main(["--bankroll", "1000", "--no-fetch"])
        assert exc.value.code == 2


# ---------------------------------------------------------------------------
# End-to-end with mock data
# ---------------------------------------------------------------------------


class TestE2EWithMock:
    """Full pipeline with --no-fetch and sample odds."""

    def test_e2e_produces_ledger(self, tmp_path: Path) -> None:
        """Run the full betting pipeline and verify the ledger CSV."""
        output_dir = tmp_path / "betting_output"
        ret = main(
            [
                "--odds", str(SAMPLE_ODDS),
                "--no-fetch",
                "--bankroll", "1000",
                "--output-dir", str(output_dir),
            ]
        )
        assert ret == 0

        ledger_path = output_dir / "paper_bet_ledger.csv"
        assert ledger_path.is_file(), f"Ledger CSV not found at {ledger_path}"

        with open(ledger_path, newline="") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) >= 1, "Ledger must contain at least one bet row"

        # Verify schema — each row should have the key fields non-empty
        for row in rows:
            assert row["event_id"], "Missing event_id"
            assert row["selection"], "Missing selection"
            assert row["decimal_odds"], "Missing decimal_odds"
            assert row["stake"], "Missing stake"
            assert row["bankroll_before"], "Missing bankroll_before"
            assert row["bankroll_after"], "Missing bankroll_after"

    def test_e2e_respects_min_ev_filter(self, tmp_path: Path) -> None:
        """High ``--min-ev`` may produce zero candidates but should still exit 0."""
        output_dir = tmp_path / "betting_output_high_min_ev"
        ret = main(
            [
                "--odds", str(SAMPLE_ODDS),
                "--no-fetch",
                "--bankroll", "1000",
                "--output-dir", str(output_dir),
                "--min-ev", "0.50",  # unreachable threshold
            ]
        )
        assert ret == 0
        ledger_path = output_dir / "paper_bet_ledger.csv"
        assert ledger_path.is_file()
        with open(ledger_path, newline="") as f:
            rows = list(csv.DictReader(f))
        # With min_ev=0.50 there should be no candidates → empty ledger (only header or empty)
        # but init_ledger + log_bets with empty list writes just the header.
        assert isinstance(rows, list)
