"""Tests for the command-line interface (src/cli.py).

These tests drive the CLI as a subprocess via ``python -m src.cli`` so the
argparse surface and the ``main()`` orchestrator are exercised end-to-end
without polluting the test process state.

The ``--no-fetch`` flag is used in every test that would otherwise hit the
IMF or BIS APIs.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run ``python -m src.cli <args>`` as a subprocess from the project root."""
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
    )


def _find_predictions_csv(out_dir: Path) -> Path:
    """Return the path of the predictions CSV written by the CLI.

    Resolves the actual filename used by whichever output backend is
    available: ``world_cup_predictions.csv`` when :mod:`src.output` is
    importable, ``predictions.csv`` when the CLI falls back to its
    built-in writer.
    """
    for name in ("world_cup_predictions.csv", "predictions.csv"):
        candidate = out_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No predictions CSV found in {out_dir} "
        f"(looked for world_cup_predictions.csv, predictions.csv)"
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_help_flag() -> None:
    """``--help`` prints usage, lists every documented flag, and exits 0."""
    result = _run_cli("--help")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    combined = (result.stdout + result.stderr).lower()
    assert "usage" in combined
    # Every advertised flag must be present in the help text
    for flag in ("--seed", "--cutoff-date", "--output-dir", "--no-fetch"):
        assert flag in result.stdout, f"missing {flag} in --help output"


def test_seed_no_fetch_runs(tmp_path: Path) -> None:
    """``--seed 42 --no-fetch`` runs successfully end-to-end with mock data."""
    out_dir = tmp_path / "output"

    result = _run_cli(
        "--seed", "42",
        "--no-fetch",
        "--cutoff-date", "2026-06-20",
        "--output-dir", str(out_dir),
    )

    assert result.returncode == 0, (
        f"CLI failed with stderr:\n{result.stderr}\nstdout:\n{result.stdout}"
    )
    assert out_dir.exists() and out_dir.is_dir()
    assert "Generated" in result.stdout
    assert "predictions" in result.stdout.lower()
    assert _find_predictions_csv(out_dir).exists()


def test_cutoff_date_filter(tmp_path: Path) -> None:
    """``--cutoff-date 2026-06-20`` excludes matches with earlier dates."""
    out_dir = tmp_path / "output"

    result = _run_cli(
        "--seed", "42",
        "--no-fetch",
        "--cutoff-date", "2026-06-20",
        "--output-dir", str(out_dir),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"

    csv_path = _find_predictions_csv(out_dir)
    assert csv_path.exists(), "predictions CSV not produced"

    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    assert rows, "predictions CSV is empty"

    for row in rows:
        date = row.get("date", "")
        assert date >= "2026-06-20", (
            f"Found prediction with date {date!r} before cutoff 2026-06-20"
        )

    assert not any(r.get("match_number") == "5" for r in rows), (
        "Match #5 (2026-06-13, status 'today') leaked through cutoff filter"
    )
    assert not any(r.get("match_number") == "1" for r in rows), (
        "Match #1 (2026-06-11, status 'played') leaked through cutoff filter"
    )


def test_output_dir_created(tmp_path: Path) -> None:
    """A non-existent ``--output-dir`` is auto-created by the CLI."""
    # Nested path that definitely does not exist yet
    out_dir = tmp_path / "fresh" / "nested" / "output"
    assert not out_dir.exists()

    result = _run_cli(
        "--seed", "42",
        "--no-fetch",
        "--cutoff-date", "2026-06-20",
        "--output-dir", str(out_dir),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out_dir.exists(), "output directory was not created"
    assert out_dir.is_dir()
    # And it should actually be populated
    assert any(out_dir.iterdir()), "output directory is empty"


def test_invalid_date() -> None:
    """``--cutoff-date not-a-date`` causes argparse to reject the argument.

    argparse uses exit code 2 for argument-validation errors and writes a
    human-readable message to stderr.
    """
    result = _run_cli("--cutoff-date", "not-a-date")
    assert result.returncode == 2, (
        f"expected exit 2 from argparse, got {result.returncode}; "
        f"stderr: {result.stderr}"
    )
    combined = (result.stdout + result.stderr).lower()
    assert "invalid" in combined or "error" in combined
    # The offending value should be quoted back in the error message
    assert "not-a-date" in result.stderr


def test_pyproject_script_entry_point() -> None:
    """``pyproject.toml`` declares ``predict = "src.cli:main"`` as a script."""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
    assert "[project.scripts]" in pyproject, "missing [project.scripts] section"
    assert "predict" in pyproject
    assert "src.cli:main" in pyproject
