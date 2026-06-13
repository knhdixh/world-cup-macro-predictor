"""Schema and validation for World-Cup economic-metric records.

The pipeline ingests a list of ``EconData`` records (one per nation) and
runs them through :func:`validate_econ_data` before any downstream math.
Validation is **warn-only by design**: bad ranges produce a human-readable
warning string, the record is kept, and the function never raises.

Why warn-only?
    The downstream prediction is a ranking, not a financial decision.
    A single bad record from a flaky API call should not abort the whole
    batch — log it, surface it, let a human triage.

The range bounds below are deliberately generous so that real-world
outliers (Turkey 80% inflation, Japan 255% debt/GDP, Curaçao 150K pop)
pass without warning. See ``tests/test_validation.py`` for the
representative values that must NOT warn.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class EconData:
    """One nation's worth of economic indicators.

    Field semantics
    ---------------
    iso3      : ISO-3166-1 alpha-3 country code (e.g. ``"USA"``, ``"DEU"``).
    pop       : population, absolute count (not in millions).
    gdp       : real GDP growth, percent (e.g. ``2.5`` = 2.5%).
    infl      : CPI inflation, percent (e.g. ``40.0`` = 40%).
    unemp     : unemployment, **decimal fraction** (e.g. ``0.04`` = 4%).
    rate      : central-bank policy rate, percent.
    debt_gdp  : public debt / GDP, **decimal fraction** (e.g. ``2.55`` = 255%).
    source    : provenance string (e.g. ``"World Bank 2024"``).
    """
    iso3: str
    pop: Optional[int]
    gdp: Optional[float]
    infl: Optional[float]
    unemp: Optional[float]
    rate: Optional[float]
    debt_gdp: Optional[float]
    source: Optional[str]


# ---------------------------------------------------------------------------
# Range bounds (inclusive) — must match the test file's contract
# ---------------------------------------------------------------------------

_POP_MIN = 0                       # strictly positive is enforced separately
_GDP_MIN, _GDP_MAX = -20.0, 30.0    # percent
_INFL_MIN, _INFL_MAX = -5.0, 200.0  # percent
_UNEMP_MIN, _UNEMP_MAX = 0.001, 0.5  # decimal fraction (0.1% .. 50%)
_RATE_MIN, _RATE_MAX = -2.0, 50.0   # percent
_DEBT_MIN, _DEBT_MAX = 0.0, 3.0     # decimal fraction (0% .. 300%)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_econ_data(
    data: List[EconData],
) -> Tuple[List[EconData], List[str]]:
    """Validate a batch of ``EconData`` records. Warn-only — never raises.

    Performs per-record range checks and per-record missing-value checks.
    Returns the input list unchanged plus a list of human-readable warning
    strings. An empty ``warnings`` list means every record passed every
    range/None check.

    The 48-nation completeness check is exposed separately via
    :func:`check_all_nations_present` so that small unit-test fixtures
    (1 record, partial batches) don't generate spurious "missing
    nations" warnings. Callers that care about tournament-wide coverage
    should call both functions and concatenate the warning lists.

    Returns
    -------
    (validated_data, warnings)
        ``validated_data`` is the input list, unchanged.
        ``warnings`` is a list of human-readable strings describing every
        problem found. The list is empty when the batch is clean.
    """
    warnings: List[str] = []

    for record in data:
        _check_record(record, warnings)

    _check_unique_iso3(data, warnings)

    return data, warnings


def check_all_nations_present(
    data: List[EconData],
) -> List[str]:
    """Return warnings if the batch does not cover all 48 World Cup nations.

    Always available, but no-op if ``src.country_map`` cannot be imported.
    Never raises. Returns an empty list when every qualified team is
    present.
    """
    warnings: List[str] = []
    _check_completeness(data, warnings)
    return warnings


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _check_completeness(data: List[EconData], warnings: List[str]) -> None:
    """Warn if the batch doesn't cover all 48 World Cup nations."""
    try:
        from src.country_map import COUNTRY_MAP  # local import — keeps module importable without it
        expected = {entry["iso3"] for entry in COUNTRY_MAP}
    except Exception as exc:  # pragma: no cover - defensive: never crash on missing map
        logger.debug("country_map unavailable, skipping 48-nation completeness check: %s", exc)
        return

    present = {r.iso3 for r in data if r.iso3}
    missing = expected - present
    if missing:
        sample = ", ".join(sorted(missing)[:5])
        warnings.append(
            f"missing nations: expected 48 qualified teams, found {len(present)}; "
            f"missing={sample}{'...' if len(missing) > 5 else ''}"
        )


def _check_unique_iso3(data: List[EconData], warnings: List[str]) -> None:
    """Warn on duplicate iso3 codes within a single batch."""
    seen: set[str] = set()
    dups: set[str] = set()
    for record in data:
        if record.iso3 and record.iso3 in seen:
            dups.add(record.iso3)
        seen.add(record.iso3)
    for iso3 in sorted(dups):
        warnings.append(f"duplicate iso3 in batch: {iso3!r}")


def _check_record(record: EconData, warnings: List[str]) -> None:
    """Apply every range check to a single record. Never raises."""
    iso3 = record.iso3 or "<unknown-iso3>"

    # --- pop ---
    if record.pop is None:
        warnings.append(f"{iso3}: pop is None (missing)")
    elif not isinstance(record.pop, (int, float)) or isinstance(record.pop, bool):
        warnings.append(f"{iso3}: pop has wrong type ({type(record.pop).__name__})")
    elif record.pop <= _POP_MIN:
        warnings.append(f"{iso3}: pop={record.pop} is not positive")

    # --- gdp ---
    _range_check(record.gdp, "gdp", iso3, _GDP_MIN, _GDP_MAX, warnings, unit="%")

    # --- infl ---
    _range_check(record.infl, "infl", iso3, _INFL_MIN, _INFL_MAX, warnings, unit="%")

    # --- unemp ---
    _range_check(record.unemp, "unemp", iso3, _UNEMP_MIN, _UNEMP_MAX,
                 warnings, unit="(decimal)")

    # --- rate ---
    _range_check(record.rate, "rate", iso3, _RATE_MIN, _RATE_MAX, warnings, unit="%")

    # --- debt_gdp ---
    _range_check(record.debt_gdp, "debt_gdp", iso3, _DEBT_MIN, _DEBT_MAX,
                 warnings, unit="(decimal)")


def _range_check(
    value: Any,
    field: str,
    iso3: str,
    lo: float,
    hi: float,
    warnings: List[str],
    *,
    unit: str = "",
) -> None:
    """Emit a warning if ``value`` is None, non-numeric, or out of [lo, hi]."""
    if value is None:
        warnings.append(f"{iso3}: {field} is None (missing)")
        return
    # bools are ints in Python — exclude them.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        warnings.append(
            f"{iso3}: {field} has wrong type ({type(value).__name__}), expected numeric"
        )
        return
    if value < lo or value > hi:
        unit_str = f" {unit}" if unit else ""
        warnings.append(
            f"{iso3}: {field}={value}{unit_str} out of range [{lo}, {hi}]"
        )


__all__ = ["EconData", "validate_econ_data"]
