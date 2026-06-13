"""IMF WEO DataMapper API v1 client.

Fetches five headline indicators for a list of ISO-3 countries and returns
them as a normalised dictionary with unit conversions applied.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

# Indicator code → internal key mapping
_INDICATORS = {
    "NGDP_RPCH": "gdp",       # Real GDP growth (%)
    "PCPIPCH": "infl",        # Inflation (%)
    "LUR": "unemp",           # Unemployment rate (%)
    "GGXWDG_NGDP": "debt_gdp",  # General government gross debt (% of GDP)
    "LP": "pop",              # Population (millions)
}


def _apply_unit_conversion(key: str, raw_value: float | None) -> float | None:
    """Apply required unit conversions to a raw IMF value.

    * LP  (population millions)  → multiply by 1_000_000
    * LUR (unemployment %)       → divide by 100 (decimal)
    * GGXWDG_NGDP (debt % GDP)   → divide by 100 (ratio)
    * NGDP_RPCH & PCPIPCH        → keep as-is (already percentage form)
    """
    if raw_value is None:
        return None
    if key == "pop":
        return raw_value * 1_000_000
    if key in ("unemp", "debt_gdp"):
        return raw_value / 100
    return raw_value


def fetch_imf_data(countries_iso3: List[str], year: int = 2026) -> Dict[str, dict]:
    """Fetch IMF WEO indicators for *countries_iso3* for the given *year*.

    Returns a dictionary keyed by ISO-3 code. Each value is a sub-dict
    containing the keys ``pop``, ``gdp``, ``infl``, ``unemp``,
    ``debt_gdp`` and ``source``.

    The function issues one HTTP request per indicator (5 total) with a
    0.3-second sleep between calls.  Network or HTTP errors for a single
    indicator are logged and skipped so that partial data is still returned.
    """
    if not countries_iso3:
        return {}

    # Pre-seed result structure so every country has a record even if an
    # indicator request fails entirely.
    result: Dict[str, dict] = {}
    for iso3 in countries_iso3:
        result[iso3] = {
            "pop": None,
            "gdp": None,
            "infl": None,
            "unemp": None,
            "debt_gdp": None,
            "source": f"IMF WEO {year}",
        }

    countries_path = ",".join(countries_iso3)
    year_str = str(year)

    for indicator_code, key in _INDICATORS.items():
        url = f"{BASE_URL}/{indicator_code}/{countries_path}?periods={year}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to fetch %s: %s", indicator_code, exc)
            time.sleep(0.3)
            continue

        values = data.get("values", {}).get(indicator_code, {})
        for iso3 in countries_iso3:
            country_data = values.get(iso3)
            if country_data is None:
                logger.warning(
                    "Indicator %s missing for country %s in year %s",
                    indicator_code,
                    iso3,
                    year,
                )
                result[iso3][key] = None
                continue

            raw_value = country_data.get(year_str)
            if raw_value is None:
                logger.warning(
                    "Indicator %s has null value for country %s in year %s",
                    indicator_code,
                    iso3,
                    year,
                )
            result[iso3][key] = _apply_unit_conversion(key, raw_value)

        time.sleep(0.3)

    return result
