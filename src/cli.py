"""Command-line interface for the football-prediction pipeline.

Orchestrates the full prediction pipeline:

1. Load country / FIFA reference data
2. Fetch IMF and BIS data (or use mock data with ``--no-fetch``)
3. Build and normalise the unified dataset
4. Pick upcoming World Cup matches as of ``--cutoff-date``
5. Predict every upcoming match
6. Write the results to ``--output-dir`` as CSV (and Excel when
   :mod:`src.output` is available)

The CLI is intentionally thin — it glues the existing modules together and
adds the user-facing surface (argparse, file I/O, progress logging).  All
business logic lives in :mod:`src.aggregate`, :mod:`src.predict` and
:mod:`src.schedule`.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Pipeline modules
# ---------------------------------------------------------------------------
from src.aggregate import build_dataset, normalize_scores
from src.country_map import COUNTRY_MAP, get_iso3
from src.fifa_data import FIFA_DATA
from src.predict import predict_all_upcoming
from src.schedule import get_upcoming_matches

# Optional: src.output is implemented in a parallel task.  If it is
# available we delegate CSV / Excel generation to it; otherwise we fall
# back to a minimal CSV writer so the CLI still works.
try:
    from src.output import generate_csv, generate_excel  # type: ignore[import-not-found]

    _HAS_OUTPUT_MODULE = True
except Exception:  # pragma: no cover - exercised when src.output is missing
    generate_csv = None  # type: ignore[assignment]
    generate_excel = None  # type: ignore[assignment]
    _HAS_OUTPUT_MODULE = False

logger = logging.getLogger(__name__)

__all__ = ["build_parser", "main", "_mock_data", "_write_fallback_csv"]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

DEFAULT_CUTOFF_DATE = "2026-06-13"
DEFAULT_OUTPUT_DIR = "./output"
DEFAULT_SEED = 42


def _valid_iso_date(value: str) -> str:
    """Argparse type validator for ISO ``YYYY-MM-DD`` dates.

    Raises :class:`argparse.ArgumentTypeError` on bad input so argparse
    prints a clean error and exits with status 2.
    """
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date: {value!r} (expected YYYY-MM-DD)"
        ) from exc
    return value


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Exposed as a public helper so tests (and other callers) can inspect
    or extend the parser without invoking :func:`main`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m src.cli",
        description=(
            "World Cup 2026 prediction pipeline.  Combines FIFA rankings "
            "with IMF / BIS economic indicators to forecast every match "
            "still to be played as of the given cutoff date."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Reproducibility seed for the noise added to expected goals.",
    )
    parser.add_argument(
        "--cutoff-date",
        type=_valid_iso_date,
        default=DEFAULT_CUTOFF_DATE,
        metavar="YYYY-MM-DD",
        help=(
            "ISO date treated as 'today'.  Matches with status 'played' or "
            "'today' are excluded; only 'upcoming' / 'knockout' matches on "
            "or after this date are predicted."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(DEFAULT_OUTPUT_DIR),
        help="Directory where predictions.csv (and predictions.xlsx) are written.",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        default=False,
        help=(
            "Skip IMF / BIS HTTP calls and use internal mock data instead. "
            "Useful for testing and offline runs."
        ),
    )
    return parser


# ---------------------------------------------------------------------------
# Mock data (for --no-fetch and tests)
# ---------------------------------------------------------------------------

# Plausible mid-range values that keep ``compute_econ_score`` happy:
#   pop      : 50M  → log10(pop)-6 ≈ 1.7   (population term > 0)
#   gdp      : 2.5  (% growth)              (formula expects percentage)
#   infl     : 3.0  (% inflation)
#   unemp    : 0.05 (DECIMAL — see formula.py docstring)
#   rate     : 3.0  (% policy rate)
#   debt_gdp : 0.6  (ratio)
_MOCK_POP = 50_000_000.0
_MOCK_GDP = 2.5
_MOCK_INFL = 3.0
_MOCK_UNEMP = 0.05
_MOCK_RATE = 3.0
_MOCK_DEBT_GDP = 0.6


def _mock_data(
    country_map: List[Dict[str, str]] = COUNTRY_MAP,
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """Generate plausible mock IMF and BIS data for *every* country in *country_map*.

    Returns a 2-tuple ``(imf_data, bis_rates)`` with shapes matching
    :func:`src.imf_fetcher.fetch_imf_data` and
    :func:`src.bis_fetcher.fetch_all_policy_rates` respectively, so the
    result can be passed straight to :func:`src.aggregate.build_dataset`.

    Parameters
    ----------
    country_map:
        List of country entries (each must contain an ``"iso3"`` key).
        Defaults to the project-wide :data:`src.country_map.COUNTRY_MAP`.

    Returns
    -------
    tuple
        ``(imf_data, bis_rates)`` — both keyed by ISO-3 code.
    """
    imf_data: Dict[str, Dict[str, float]] = {}
    bis_rates: Dict[str, float] = {}
    for entry in country_map:
        iso3 = entry["iso3"]
        imf_data[iso3] = {
            "pop": _MOCK_POP,
            "gdp": _MOCK_GDP,
            "infl": _MOCK_INFL,
            "unemp": _MOCK_UNEMP,
            "debt_gdp": _MOCK_DEBT_GDP,
        }
        bis_rates[iso3] = _MOCK_RATE
    return imf_data, bis_rates


# ---------------------------------------------------------------------------
# Fallback CSV writer (used when src.output is unavailable)
# ---------------------------------------------------------------------------

_FALLBACK_CSV_FIELDS = [
    "date",
    "team_a_iso3",
    "team_b_iso3",
    "predicted_score",
    "team_a_xg",
    "team_b_xg",
    "team_a_blended",
    "team_b_blended",
]


def _write_fallback_csv(
    predictions: List[Dict[str, Any]],
    matches: List[Dict[str, Any]],
    output_dir: Path,
) -> Path:
    """Write *predictions* to ``output_dir/predictions.csv`` using :mod:`csv`.

    Each prediction is zipped with the originating schedule *match* so the
    CSV carries the match date.  ISO-3 codes are surfaced as the
    ``team_a_iso3`` / ``team_b_iso3`` columns.

    Returns the path of the written CSV.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "predictions.csv"

    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FALLBACK_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for match, pred in zip(matches, predictions):
            row = {
                "date": match.get("date", ""),
                "team_a_iso3": pred.get("team_a", ""),
                "team_b_iso3": pred.get("team_b", ""),
                "predicted_score": pred.get("predicted_score", ""),
                "team_a_xg": pred.get("team_a_xg", ""),
                "team_b_xg": pred.get("team_b_xg", ""),
                "team_a_blended": pred.get("team_a_blended", ""),
                "team_b_blended": pred.get("team_b_blended", ""),
            }
            writer.writerow(row)
    return csv_path


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------


def _convert_match_to_iso3(match: Dict[str, Any]) -> Dict[str, Any] | None:
    """Return a copy of *match* with ``team_a`` / ``team_b`` mapped to ISO-3.

    Returns ``None`` if either side cannot be resolved (e.g. knockout
    placeholders like ``"1A"`` or ``"W73"``).  The caller is expected to
    skip ``None`` results.
    """
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


def _fetch_live_data(
    country_map: List[Dict[str, str]],
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    """Fetch IMF + BIS data for every country in *country_map*.

    Imports are local so the modules can be mocked or unavailable
    without breaking module import.  In practice both fetchers are part
    of this project and will be present at runtime.
    """
    from src.bis_fetcher import fetch_all_policy_rates
    from src.imf_fetcher import fetch_imf_data

    iso3_codes = [entry["iso3"] for entry in country_map]
    logger.info("Fetching IMF data for %d countries…", len(iso3_codes))
    imf_data = fetch_imf_data(iso3_codes)
    logger.info("Fetching BIS policy rates for %d countries…", len(iso3_codes))
    bis_rates = fetch_all_policy_rates(iso3_codes)
    return imf_data, bis_rates


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the full prediction pipeline.  Returns the process exit code."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = build_parser().parse_args(argv)

    # 0. Ensure output directory exists (also done lazily in writers, but
    #    we do it up front so the user gets immediate feedback).
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directory: %s", args.output_dir)

    # 1. Reference data is module-level — nothing to load.

    # 2. Fetch (or mock) IMF + BIS data.
    if args.no_fetch:
        logger.info("--no-fetch set; using internal mock data")
        imf_data, bis_rates = _mock_data(COUNTRY_MAP)
    else:
        imf_data, bis_rates = _fetch_live_data(COUNTRY_MAP)

    # 3. Build the unified, normalised dataset.
    dataset = build_dataset(imf_data, bis_rates, FIFA_DATA, COUNTRY_MAP)
    dataset = normalize_scores(dataset)
    logger.info("Dataset built: %d rows", len(dataset))

    # 4. Pick upcoming matches as of the cutoff date.
    upcoming = get_upcoming_matches(args.cutoff_date)
    logger.info(
        "Upcoming matches on/after %s: %d", args.cutoff_date, len(upcoming)
    )

    # 5. Convert FIFA team names to ISO-3 and drop unresolvable matches
    #    (knockout placeholders like "1A", "W73" — they will be predicted
    #    in a later task once group results are known).
    resolved = [m for m in (_convert_match_to_iso3(m) for m in upcoming) if m is not None]
    skipped = len(upcoming) - len(resolved)
    if skipped:
        logger.info("Skipped %d unresolvable match(es) (knockout placeholders)", skipped)

    # 6. Predict every resolved match.
    predictions = predict_all_upcoming(resolved, dataset, seed=args.seed)
    logger.info("Generated %d predictions", len(predictions))

    # 7. Write outputs (CSV always; Excel when src.output is available).
    if _HAS_OUTPUT_MODULE and generate_csv is not None:
        csv_path = generate_csv(predictions, resolved, args.output_dir)
        try:
            generate_excel(
                predictions, resolved, args.output_dir,
                seed_used=args.seed, cutoff_date=args.cutoff_date,
            )  # type: ignore[misc]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Excel generation failed: %s", exc)
    else:
        logger.info("src.output unavailable — writing fallback CSV")
        csv_path = _write_fallback_csv(predictions, resolved, args.output_dir)

    # 8. Summary
    print(f"Generated {len(predictions)} predictions. Output: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
