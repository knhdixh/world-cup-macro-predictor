"""Unified odds provider registry — CSV and API sources."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.betting.api_odds import ApiOddsProvider
from src.betting.odds import CsvOddsProvider


class OddsProviderRegistry:
    """Registry for multiple odds providers with a unified interface.

    Supports:
    - csv: Read from a CSV file (Phase 1 compatible)
    - api: Fetch from The Odds API (Phase 2)
    - auto: Try API first, fall back to CSV
    """

    def __init__(self, csv_path: str | Path | None = None, api_key: str | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else None
        self.api_key = api_key

    def get_odds(self, method: str = "csv", **kwargs) -> list[dict[str, Any]]:
        """Fetch odds using the specified method.

        Parameters
        ----------
        method : str
            "csv" — read from CSV file
            "api" — fetch from The Odds API
            "auto" — try API, fall back to CSV

        Returns
        -------
        list[dict]
            Odds data in Phase 1 CSV schema format.
        """
        if method == "csv":
            return self._get_csv_odds()

        if method == "api":
            return self._get_api_odds(**kwargs)

        if method == "auto":
            try:
                return self._get_api_odds(**kwargs)
            except (RuntimeError, ValueError):
                return self._get_csv_odds()

        raise ValueError(f"Unknown odds method: {method!r}")

    def _get_csv_odds(self) -> list[dict[str, Any]]:
        if self.csv_path is None:
            raise ValueError("csv_path must be set to use method='csv'")
        return CsvOddsProvider(self.csv_path).fetch_odds()

    def _get_api_odds(self, **kwargs) -> list[dict[str, Any]]:
        provider = ApiOddsProvider(api_key=self.api_key)
        return provider.fetch_odds(
            sport=kwargs.get("sport", "soccer_world_cup"),
            regions=kwargs.get("regions", "uk"),
            markets=kwargs.get("markets", "h2h"),
        )
