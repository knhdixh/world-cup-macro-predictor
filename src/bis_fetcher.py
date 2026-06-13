"""BIS central bank policy rate fetcher via SDMX API.

Fetches the latest policy rate for a given country ISO2 code from the
Bank for International Settlements (BIS) statistics API (XML response).
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET

import requests

BASE_URL = "https://stats.bis.org/api/v1/data/WS_CBPOL/M.{iso2}"
TIMEOUT = 10

logger = logging.getLogger(__name__)

# SDMX XML namespace for the data message
_NS = "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"


def fetch_policy_rate(iso2: str) -> float | None:
    """Fetch the latest central bank policy rate for a country.

    Args:
        iso2: ISO 3166-1 alpha-2 country code (e.g., "US", "FR").

    Returns:
        The latest policy rate as a float, or None if no data is available.
    """
    url = BASE_URL.format(iso2=iso2)
    params = {"lastNObservations": "1"}

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError:
        return None

    obs = root.find(".//Obs")
    if obs is not None and obs.get("OBS_VALUE"):
        try:
            return float(obs.get("OBS_VALUE"))
        except (ValueError, TypeError):
            return None

    return None


def fetch_all_policy_rates(countries_iso3: list[str]) -> dict[str, float | None]:
    """Fetch policy rates for multiple countries.

    Args:
        countries_iso3: List of ISO 3166-1 alpha-3 country codes.

    Returns:
        Dictionary mapping each ISO3 code to its policy rate (or None).
    """
    from src.country_map import get_iso2

    results: dict[str, float | None] = {}
    for i, iso3 in enumerate(countries_iso3):
        try:
            iso2 = get_iso2(iso3)
        except KeyError:
            logger.warning("No ISO-2 mapping for %s; setting rate to None", iso3)
            results[iso3] = None
            if i < len(countries_iso3) - 1:
                time.sleep(0.3)
            continue
        results[iso3] = fetch_policy_rate(iso2)
        if i < len(countries_iso3) - 1:
            time.sleep(0.3)
    return results
