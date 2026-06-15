"""Tests for the core prediction engine (src/predict.py)."""

from __future__ import annotations

import random
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.predict import (
    apply_noise,
    blended_to_xg,
    compute_blended_score,
    predict_all_upcoming,
    predict_match,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    """Minimal dataset with enough rows for lopsided and close-match tests."""
    return pd.DataFrame(
        [
            {"iso3": "FRA", "norm_fifa": 1.0, "norm_econ": 0.90, "econ_score": 4.5, "fifa_points": 1800.0},
            {"iso3": "NZL", "norm_fifa": 0.0, "norm_econ": 0.10, "econ_score": 0.5, "fifa_points": 800.0},
            {"iso3": "USA", "norm_fifa": 0.65, "norm_econ": 0.65, "econ_score": 3.0, "fifa_points": 1500.0},
            {"iso3": "CAN", "norm_fifa": 0.55, "norm_econ": 0.60, "econ_score": 2.8, "fifa_points": 1400.0},
            {"iso3": "DEU", "norm_fifa": 0.90, "norm_econ": 0.85, "econ_score": 4.0, "fifa_points": 1700.0},
            {"iso3": "BRA", "norm_fifa": 0.95, "norm_econ": 0.70, "econ_score": 3.5, "fifa_points": 1750.0},
            {"iso3": "ARG", "norm_fifa": 0.92, "norm_econ": 0.60, "econ_score": 3.0, "fifa_points": 1720.0},
            {"iso3": "JPN", "norm_fifa": 0.75, "norm_econ": 0.80, "econ_score": 3.8, "fifa_points": 1600.0},
        ]
    )


@pytest.fixture
def ten_matches() -> list[dict[str, Any]]:
    """Ten synthetic upcoming matches for predict_all_upcoming tests."""
    return [
        {"team_a": "FRA", "team_b": "NZL"},
        {"team_a": "USA", "team_b": "CAN"},
        {"team_a": "DEU", "team_b": "BRA"},
        {"team_a": "ARG", "team_b": "JPN"},
        {"team_a": "FRA", "team_b": "DEU"},
        {"team_a": "NZL", "team_b": "CAN"},
        {"team_a": "USA", "team_b": "BRA"},
        {"team_a": "ARG", "team_b": "FRA"},
        {"team_a": "JPN", "team_b": "DEU"},
        {"team_a": "CAN", "team_b": "NZL"},
    ]


# ---------------------------------------------------------------------------
# compute_blended_score
# ---------------------------------------------------------------------------

def test_blend_50_50() -> None:
    """Exact 50/50 blend of two scores."""
    assert compute_blended_score(0.8, 0.6) == pytest.approx(0.7)


def test_blend_bounds() -> None:
    """Blending at the extremes of [0, 1] stays at the extremes."""
    assert compute_blended_score(0.0, 0.0) == pytest.approx(0.0)
    assert compute_blended_score(1.0, 1.0) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# blended_to_xg
# ---------------------------------------------------------------------------

def test_xg_conversion() -> None:
    """Linear mapping from blended score to expected goals."""
    assert blended_to_xg(0.5) == pytest.approx(2.0)
    assert blended_to_xg(1.0) == pytest.approx(4.0)
    assert blended_to_xg(0.0) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# apply_noise
# ---------------------------------------------------------------------------

def test_noise_reproducible() -> None:
    """Same seed must yield identical noise values."""
    first = apply_noise(2.0, seed=42)
    second = apply_noise(2.0, seed=42)
    assert first == pytest.approx(second)


def test_noise_clamp() -> None:
    """Extreme noise must be clamped to the [0, 4] interval."""
    mock_rng = MagicMock()
    mock_rng.gauss.return_value = 10.0
    with patch("src.predict.random.Random", return_value=mock_rng):
        high = apply_noise(2.0, seed=99)
        assert high == 4.0

    mock_rng.gauss.return_value = -10.0
    with patch("src.predict.random.Random", return_value=mock_rng):
        low = apply_noise(2.0, seed=99)
        assert low == 0.0


# ---------------------------------------------------------------------------
# predict_match
# ---------------------------------------------------------------------------

def test_lopsided_match(sample_dataset: pd.DataFrame) -> None:
    """France (strong) vs New Zealand (weak) → France wins by 2+ goals."""
    result = predict_match("FRA", "NZL", sample_dataset, seed=123)
    a_goals = int(result["predicted_score"].split("-")[0])
    b_goals = int(result["predicted_score"].split("-")[1])
    assert a_goals - b_goals >= 2


def test_close_match(sample_dataset: pd.DataFrame) -> None:
    """USA vs Canada → close game, goal difference at most 1."""
    result = predict_match("USA", "CAN", sample_dataset, seed=456)
    a_goals = int(result["predicted_score"].split("-")[0])
    b_goals = int(result["predicted_score"].split("-")[1])
    assert abs(a_goals - b_goals) <= 1


# ---------------------------------------------------------------------------
# predict_all_upcoming
# ---------------------------------------------------------------------------

def test_predict_all(sample_dataset: pd.DataFrame, ten_matches: list[dict[str, Any]]) -> None:
    """Ten matches in → ten predictions out, each with required keys."""
    predictions = predict_all_upcoming(ten_matches, sample_dataset, seed=777)
    assert len(predictions) == len(ten_matches)

    required_keys = {
        "team_a",
        "team_b",
        "team_a_xg",
        "team_b_xg",
        "predicted_score",
        "team_a_blended",
        "team_b_blended",
        "team_a_econ",
        "team_b_econ",
        "team_a_fifa",
        "team_b_fifa",
    }
    for pred in predictions:
        assert required_keys.issubset(set(pred.keys())), f"Missing keys: {required_keys - set(pred.keys())}"
        assert isinstance(pred["predicted_score"], str)
        assert "-" in pred["predicted_score"]


def test_reproducibility(sample_dataset: pd.DataFrame, ten_matches: list[dict[str, Any]]) -> None:
    """Identical seed must produce identical predictions for every match."""
    first = predict_all_upcoming(ten_matches, sample_dataset, seed=12345)
    second = predict_all_upcoming(ten_matches, sample_dataset, seed=12345)
    for a, b in zip(first, second):
        assert a == b
