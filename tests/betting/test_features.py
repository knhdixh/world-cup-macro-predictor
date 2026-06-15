"""Tests for betting feature engineering — Elo, squad value, form."""

from __future__ import annotations

import math

import pytest

from src.betting.features import EloSystem, compute_elo_features


class TestEloSystem:
    """Tests for the Elo rating system."""

    def test_elo_expected_score(self) -> None:
        """Equal ratings → 0.5; 400 point difference → ~0.91."""
        elo = EloSystem()

        # Equal ratings
        p_equal = elo.expected_score(1500.0, 1500.0)
        assert p_equal == 0.5

        # 400 point difference → expected ≈ 0.909
        p_strong = elo.expected_score(1900.0, 1500.0)
        expected = 1.0 / (1.0 + math.pow(10.0, (1500.0 - 1900.0) / 400.0))
        assert p_strong == pytest.approx(expected, rel=1e-9)
        assert p_strong == pytest.approx(0.909, abs=0.01)

    def test_elo_update_win(self) -> None:
        """After 1500 vs 1500 with home win → home increases, away decreases."""
        elo = EloSystem()
        new_a, new_b = elo.update_ratings("FRA", "BRA", goals_a=3, goals_b=1)

        # Both started at 1500
        # E_A = 0.5, S_A = 1.0 → new = 1500 + 32 * (1.0 - 0.5) = 1516
        # E_B = 0.5, S_B = 0.0 → new = 1500 + 32 * (0.0 - 0.5) = 1484
        assert new_a == pytest.approx(1516.0)
        assert new_b == pytest.approx(1484.0)
        assert new_a > 1500.0
        assert new_b < 1500.0
        # Sum should remain 3000 (conservation)
        assert new_a + new_b == pytest.approx(3000.0)

    def test_elo_update_draw(self) -> None:
        """After 1500 vs 1500 with draw → no change."""
        elo = EloSystem()
        new_a, new_b = elo.update_ratings("FRA", "BRA", goals_a=1, goals_b=1)

        # Both started at 1500
        # E_A = 0.5, S_A = 0.5 → new = 1500 + 32 * (0.5 - 0.5) = 1500
        assert new_a == pytest.approx(1500.0)
        assert new_b == pytest.approx(1500.0)

    def test_elo_features_structure(self) -> None:
        """compute_elo_features returns correct keys."""
        elo = EloSystem()
        features = compute_elo_features("FRA", "BRA", elo)

        assert isinstance(features, dict)
        assert set(features.keys()) == {"elo_a", "elo_b", "elo_diff", "elo_win_prob_a"}
        assert features["elo_a"] == 1500.0
        assert features["elo_b"] == 1500.0
        assert features["elo_diff"] == 0.0
        assert features["elo_win_prob_a"] == 0.5
