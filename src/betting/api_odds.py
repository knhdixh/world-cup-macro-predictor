"""Live odds provider using The Odds API."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.request import Request, urlopen


ODDS_API_BASE = "https://api.the-odds-api.com/v4"


class ApiOddsProvider:
    """Fetches live odds from The Odds API.

    Requires ODDS_API_KEY environment variable.

    Implements the OddsProvider protocol defined in Phase 1.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ODDS_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "ODDS_API_KEY not set. Get a free key at https://the-odds-api.com/"
            )

    def fetch_odds(
        self,
        sport: str = "soccer_world_cup",
        regions: str = "uk",
        markets: str = "h2h",
    ) -> list[dict[str, Any]]:
        """Fetch odds from the API and transform to Phase 1 CSV schema format.

        Returns list of dicts matching the Phase 1 CSV schema:
        timestamp, event_id, kickoff, home, away, book, market, selection, line, decimal_odds

        For each event and each bookmaker, creates one row per selection.

        Uses urllib (stdlib) — no external HTTP dependencies.
        """
        url = (
            f"{ODDS_API_BASE}/sports/{sport}/odds/"
            f"?regions={regions}&markets={markets}&apiKey={self.api_key}"
        )

        try:
            req = Request(url)
            with urlopen(req) as response:
                data = json.loads(response.read().decode())
        except Exception as e:
            raise RuntimeError(f"Failed to fetch odds from The Odds API: {e}") from e

        rows: list[dict[str, Any]] = []
        for event in data:
            event_id = event.get("id", "")
            kickoff = event.get("commence_time", "")
            home_team = event.get("home_team", "")
            away_team = event.get("away_team", "")

            for bookmaker in event.get("bookmakers", []):
                book_name = bookmaker.get("title", "unknown")
                for market in bookmaker.get("markets", []):
                    market_name = market.get("key", "")
                    for outcome in market.get("outcomes", []):
                        rows.append({
                            "timestamp": "",
                            "event_id": event_id,
                            "kickoff": kickoff,
                            "home": home_team,
                            "away": away_team,
                            "book": book_name,
                            "market": market_name,
                            "selection": outcome.get("name", ""),
                            "line": outcome.get("point", ""),
                            "decimal_odds": outcome.get("price", 0),
                        })

        if not rows:
            raise RuntimeError(f"No odds data returned for sport={sport}")

        return rows
