"""Tests for src/aggregate.py — dataset merging and score normalisation."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import pytest

from src.aggregate import build_dataset, normalize_scores
from src.country_map import COUNTRY_MAP
from src.formula import compute_econ_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_imf_data(country_map: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    """Generate IMF-style data for every country in *country_map*.

    Units are already converted (what fetch_imf_data returns):
      pop      : absolute count
      gdp      : percentage form
      infl     : percentage form
      unemp    : decimal form
      debt_gdp : ratio form
    """
    data: dict[str, dict[str, Any]] = {}
    for entry in country_map:
        iso3 = entry["iso3"]
        # Deterministic but varied values so tests are interesting
        base = hash(iso3) % 1000
        data[iso3] = {
            "pop": 1_000_000 + (base * 10_000),          # absolute
            "gdp": 1.0 + (base % 50) / 10.0,             # % form
            "infl": 1.0 + (base % 30) / 10.0,            # % form
            "unemp": 0.02 + (base % 80) / 1000.0,        # decimal
            "debt_gdp": 0.3 + (base % 200) / 100.0,      # ratio
            "source": "IMF WEO 2026",
        }
    return data


def _make_mock_bis_rates(country_map: list[dict[str, str]], none_iso3s: list[str] | None = None) -> dict[str, float | None]:
    """Generate BIS-style policy rates."""
    none_iso3s = none_iso3s or []
    rates: dict[str, float | None] = {}
    for entry in country_map:
        iso3 = entry["iso3"]
        if iso3 in none_iso3s:
            rates[iso3] = None
        else:
            base = hash(iso3) % 1000
            rates[iso3] = 1.0 + (base % 50) / 10.0  # % form
    return rates


def _make_mock_fifa_data(country_map: list[dict[str, str]]) -> dict[str, float]:
    """Generate FIFA-style points for every country."""
    points: dict[str, float] = {}
    for entry in country_map:
        iso3 = entry["iso3"]
        base = hash(iso3) % 1000
        points[iso3] = 1200.0 + (base % 800)
    return points


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_imf_data() -> dict[str, dict[str, Any]]:
    return _make_mock_imf_data(COUNTRY_MAP)


@pytest.fixture
def mock_bis_rates() -> dict[str, float | None]:
    return _make_mock_bis_rates(COUNTRY_MAP)


@pytest.fixture
def mock_fifa_data() -> dict[str, float]:
    return _make_mock_fifa_data(COUNTRY_MAP)


# ---------------------------------------------------------------------------
# 1. Merge dataset
# ---------------------------------------------------------------------------

def test_merge_dataset(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_bis_rates: dict[str, float | None],
    mock_fifa_data: dict[str, float],
) -> None:
    """Mock IMF + BIS + FIFA data → 48-row DataFrame with expected columns."""
    df = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 48

    expected_cols = [
        "iso3", "pop", "gdp", "infl", "unemp",
        "rate", "debt_gdp", "fifa_points", "econ_score",
    ]
    assert list(df.columns) == expected_cols

    # Every ISO3 from COUNTRY_MAP is present exactly once
    assert set(df["iso3"]) == {entry["iso3"] for entry in COUNTRY_MAP}


# ---------------------------------------------------------------------------
# 2. Unit conversions — no double apply
# ---------------------------------------------------------------------------

def test_unit_conversions_no_double_apply(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_bis_rates: dict[str, float | None],
    mock_fifa_data: dict[str, float],
) -> None:
    """Verify passed-in data has correct units and build_dataset does NOT re-apply conversions."""
    # Pick a representative country
    iso3 = "USA"
    # Set known, correctly-converted values
    mock_imf_data[iso3] = {
        "pop": 330_000_000,   # absolute (already ×1_000_000)
        "gdp": 2.5,           # % form
        "infl": 3.0,          # % form
        "unemp": 0.04,        # decimal (already ÷100)
        "debt_gdp": 1.20,     # ratio (already ÷100)
        "source": "IMF WEO 2026",
    }
    mock_bis_rates[iso3] = 5.0   # % form
    mock_fifa_data[iso3] = 1500.0

    df = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)
    row = df.loc[df["iso3"] == iso3].iloc[0]

    # Values must be exactly what we passed in — no extra conversion
    assert row["pop"] == 330_000_000
    assert row["gdp"] == 2.5
    assert row["infl"] == 3.0
    assert row["unemp"] == 0.04
    assert row["debt_gdp"] == 1.20
    assert row["rate"] == 5.0
    assert row["fifa_points"] == 1500.0

    # Also verify that if someone accidentally passes raw IMF units,
    # the test data itself is wrong — but build_dataset must not blindly
    # re-convert.  We assert the output equals the input.
    raw_pop = 330.0  # millions (raw IMF unit)
    mock_imf_data[iso3]["pop"] = raw_pop
    df2 = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)
    row2 = df2.loc[df2["iso3"] == iso3].iloc[0]
    # build_dataset must NOT convert again → value stays 330 (wrong unit, but that's the caller's fault)
    assert row2["pop"] == raw_pop


# ---------------------------------------------------------------------------
# 3. Missing BIS fallback
# ---------------------------------------------------------------------------

def test_missing_bis_fallback(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_fifa_data: dict[str, float],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two countries with rate=None → filled with median of available rates, WARNING logged."""
    # Pick two countries to have missing rates
    none_iso3s = ["HTI", "CUW"]
    bis_rates = _make_mock_bis_rates(COUNTRY_MAP, none_iso3s=none_iso3s)

    with caplog.at_level(logging.WARNING):
        df = build_dataset(mock_imf_data, bis_rates, mock_fifa_data, COUNTRY_MAP)

    # All 48 rows present
    assert len(df) == 48

    # Compute median of available rates manually
    available_rates = [v for v in bis_rates.values() if v is not None]
    expected_median = float(pd.Series(available_rates).median())

    for iso3 in none_iso3s:
        row = df.loc[df["iso3"] == iso3].iloc[0]
        assert row["rate"] == pytest.approx(expected_median)

    # Warnings logged for missing rates
    assert any("rate" in rec.message.lower() or "bis" in rec.message.lower() for rec in caplog.records)


# ---------------------------------------------------------------------------
# 4. Compute econ scores
# ---------------------------------------------------------------------------

def test_compute_econ_scores(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_bis_rates: dict[str, float | None],
    mock_fifa_data: dict[str, float],
) -> None:
    """For each row compute_econ_score() from src.formula is called → correct econ_score column."""
    df = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)

    assert "econ_score" in df.columns

    for _, row in df.iterrows():
        expected = compute_econ_score(
            pop=row["pop"],
            gdp=row["gdp"],
            infl=row["infl"],
            unemp=row["unemp"],
            rate=row["rate"],
            debt_gdp=row["debt_gdp"],
        )
        assert row["econ_score"] == pytest.approx(expected, rel=1e-9)


# ---------------------------------------------------------------------------
# 5. Normalisation range
# ---------------------------------------------------------------------------

def test_normalization_range(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_bis_rates: dict[str, float | None],
    mock_fifa_data: dict[str, float],
) -> None:
    """Min-max normalise → norm_fifa in [0,1], norm_econ in [0,1], best teams near 1.0."""
    df = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)
    df_norm = normalize_scores(df)

    assert "norm_fifa" in df_norm.columns
    assert "norm_econ" in df_norm.columns

    # All values in [0, 1]
    assert df_norm["norm_fifa"].between(0.0, 1.0).all()
    assert df_norm["norm_econ"].between(0.0, 1.0).all()

    # Best FIFA team (max points) gets 1.0
    max_fifa_idx = df_norm["fifa_points"].idxmax()
    assert df_norm.loc[max_fifa_idx, "norm_fifa"] == pytest.approx(1.0)

    # Best econ score gets 1.0
    max_econ_idx = df_norm["econ_score"].idxmax()
    assert df_norm.loc[max_econ_idx, "norm_econ"] == pytest.approx(1.0)

    # Worst get 0.0
    min_fifa_idx = df_norm["fifa_points"].idxmin()
    assert df_norm.loc[min_fifa_idx, "norm_fifa"] == pytest.approx(0.0)

    min_econ_idx = df_norm["econ_score"].idxmin()
    assert df_norm.loc[min_econ_idx, "norm_econ"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 6. Reproducibility
# ---------------------------------------------------------------------------

def test_reproducibility(
    mock_imf_data: dict[str, dict[str, Any]],
    mock_bis_rates: dict[str, float | None],
    mock_fifa_data: dict[str, float],
) -> None:
    """Same input → same output."""
    df1 = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)
    df2 = build_dataset(mock_imf_data, mock_bis_rates, mock_fifa_data, COUNTRY_MAP)

    pd.testing.assert_frame_equal(df1, df2)

    df_norm1 = normalize_scores(df1)
    df_norm2 = normalize_scores(df2)

    pd.testing.assert_frame_equal(df_norm1, df_norm2)
