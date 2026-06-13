"""Scaffolding smoke tests - verify project structure and core dependencies are usable."""

from __future__ import annotations


def test_imports() -> None:
    """Verify that core runtime dependencies can be imported."""
    import openpyxl  # noqa: F401
    import pandas  # noqa: F401
    import requests  # noqa: F401

    assert pandas.__version__, "pandas should expose a __version__ attribute"
    assert requests.__version__, "requests should expose a __version__ attribute"
    assert openpyxl.__version__, "openpyxl should expose a __version__ attribute"


def test_pytest_runs() -> None:
    """Trivial assertion to confirm the test harness is wired up."""
    assert True
