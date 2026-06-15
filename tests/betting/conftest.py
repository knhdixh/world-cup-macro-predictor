from __future__ import annotations

import pytest


@pytest.fixture
def sample_xg_params() -> dict[str, float]:
    """Shared xG parameters for betting probability tests."""
    return {"lam": 2.0, "max_goals": 10}
