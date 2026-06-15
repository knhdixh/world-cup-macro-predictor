from __future__ import annotations

import pandas as pd

from src.predict import predict_match


def _sample_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"iso3": "FRA", "norm_fifa": 1.0, "norm_econ": 0.90, "econ_score": 4.5, "fifa_points": 1800.0},
            {"iso3": "NZL", "norm_fifa": 0.0, "norm_econ": 0.10, "econ_score": 0.5, "fifa_points": 800.0},
        ]
    )


def test_clean_xg_present() -> None:
    result = predict_match("FRA", "NZL", _sample_dataset(), seed=42)

    assert "team_a_clean_xg" in result
    assert "team_b_clean_xg" in result
    assert result["team_a_clean_xg"] == 3.8
    assert result["team_b_clean_xg"] == 0.2


def test_clean_xg_no_noise() -> None:
    result = predict_match("FRA", "NZL", _sample_dataset(), seed=42)

    assert result["team_a_clean_xg"] != result["team_a_xg"]
    assert result["team_b_clean_xg"] != result["team_b_xg"]
