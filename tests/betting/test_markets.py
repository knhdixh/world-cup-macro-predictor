from __future__ import annotations

import pytest

from src.betting.markets import asian_handicap_probs, dnb_probs


def test_dnb_favorite() -> None:
    probs = dnb_probs(2.0, 1.0)
    assert probs["home"] > probs["away"]


def test_dnb_sum_to_one() -> None:
    probs = dnb_probs(1.7, 1.3)
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-6)


def test_ah_minus_05() -> None:
    probs = asian_handicap_probs(0.5, 2.0, line=-0.5)
    assert probs["away"] > probs["home"]


def test_ah_plus_05() -> None:
    probs = asian_handicap_probs(2.0, 0.5, line=0.5)
    assert probs["home"] > probs["away"]
