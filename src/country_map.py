"""World Cup 2026 country reference data.

48 qualified nations across 12 groups of 4. Each entry holds the FIFA-display
name (the form used in match feeds and team rankings), the ISO-3 country code
(the standard three-letter form used in most statistical APIs), and the group
letter (A-L).

Lookups raise KeyError on unknown input so callers fail loudly rather than
silently getting None.
"""

from typing import List, Dict


COUNTRY_MAP: List[Dict[str, str]] = [
    # Group A
    {"fifa_name": "Mexico",              "iso3": "MEX", "iso2": "MX", "group": "A"},
    {"fifa_name": "South Africa",       "iso3": "ZAF", "iso2": "ZA", "group": "A"},
    {"fifa_name": "Korea Republic",     "iso3": "KOR", "iso2": "KR", "group": "A"},
    {"fifa_name": "Czechia",             "iso3": "CZE", "iso2": "CZ", "group": "A"},
    # Group B
    {"fifa_name": "Canada",              "iso3": "CAN", "iso2": "CA", "group": "B"},
    {"fifa_name": "Bosnia and Herzegovina", "iso3": "BIH", "iso2": "BA", "group": "B"},
    {"fifa_name": "Qatar",               "iso3": "QAT", "iso2": "QA", "group": "B"},
    {"fifa_name": "Switzerland",         "iso3": "CHE", "iso2": "CH", "group": "B"},
    # Group C
    {"fifa_name": "Brazil",              "iso3": "BRA", "iso2": "BR", "group": "C"},
    {"fifa_name": "Morocco",             "iso3": "MAR", "iso2": "MA", "group": "C"},
    {"fifa_name": "Haiti",               "iso3": "HTI", "iso2": "HT", "group": "C"},
    {"fifa_name": "Scotland",            "iso3": "SCO", "iso2": "GB", "group": "C"},
    # Group D
    {"fifa_name": "USA",                 "iso3": "USA", "iso2": "US", "group": "D"},
    {"fifa_name": "Paraguay",            "iso3": "PRY", "iso2": "PY", "group": "D"},
    {"fifa_name": "Australia",           "iso3": "AUS", "iso2": "AU", "group": "D"},
    {"fifa_name": "Türkiye",             "iso3": "TUR", "iso2": "TR", "group": "D"},
    # Group E
    {"fifa_name": "Germany",             "iso3": "DEU", "iso2": "DE", "group": "E"},
    {"fifa_name": "Curaçao",             "iso3": "CUW", "iso2": "CW", "group": "E"},
    {"fifa_name": "Côte d'Ivoire",       "iso3": "CIV", "iso2": "CI", "group": "E"},
    {"fifa_name": "Ecuador",             "iso3": "ECU", "iso2": "EC", "group": "E"},
    # Group F
    {"fifa_name": "Netherlands",         "iso3": "NLD", "iso2": "NL", "group": "F"},
    {"fifa_name": "Japan",               "iso3": "JPN", "iso2": "JP", "group": "F"},
    {"fifa_name": "Sweden",              "iso3": "SWE", "iso2": "SE", "group": "F"},
    {"fifa_name": "Tunisia",             "iso3": "TUN", "iso2": "TN", "group": "F"},
    # Group G
    {"fifa_name": "Belgium",             "iso3": "BEL", "iso2": "BE", "group": "G"},
    {"fifa_name": "Egypt",               "iso3": "EGY", "iso2": "EG", "group": "G"},
    {"fifa_name": "IR Iran",             "iso3": "IRN", "iso2": "IR", "group": "G"},
    {"fifa_name": "New Zealand",         "iso3": "NZL", "iso2": "NZ", "group": "G"},
    # Group H
    {"fifa_name": "Spain",               "iso3": "ESP", "iso2": "ES", "group": "H"},
    {"fifa_name": "Cabo Verde",          "iso3": "CPV", "iso2": "CV", "group": "H"},
    {"fifa_name": "Saudi Arabia",        "iso3": "SAU", "iso2": "SA", "group": "H"},
    {"fifa_name": "Uruguay",             "iso3": "URY", "iso2": "UY", "group": "H"},
    # Group I
    {"fifa_name": "France",              "iso3": "FRA", "iso2": "FR", "group": "I"},
    {"fifa_name": "Senegal",             "iso3": "SEN", "iso2": "SN", "group": "I"},
    {"fifa_name": "Iraq",                "iso3": "IRQ", "iso2": "IQ", "group": "I"},
    {"fifa_name": "Norway",              "iso3": "NOR", "iso2": "NO", "group": "I"},
    # Group J
    {"fifa_name": "Argentina",           "iso3": "ARG", "iso2": "AR", "group": "J"},
    {"fifa_name": "Algeria",             "iso3": "DZA", "iso2": "DZ", "group": "J"},
    {"fifa_name": "Austria",             "iso3": "AUT", "iso2": "AT", "group": "J"},
    {"fifa_name": "Jordan",              "iso3": "JOR", "iso2": "JO", "group": "J"},
    # Group K
    {"fifa_name": "Portugal",            "iso3": "PRT", "iso2": "PT", "group": "K"},
    {"fifa_name": "DR Congo",            "iso3": "COD", "iso2": "CD", "group": "K"},
    {"fifa_name": "Uzbekistan",          "iso3": "UZB", "iso2": "UZ", "group": "K"},
    {"fifa_name": "Colombia",            "iso3": "COL", "iso2": "CO", "group": "K"},
    # Group L
    {"fifa_name": "England",             "iso3": "GBR", "iso2": "GB", "group": "L"},
    {"fifa_name": "Croatia",             "iso3": "HRV", "iso2": "HR", "group": "L"},
    {"fifa_name": "Ghana",               "iso3": "GHA", "iso2": "GH", "group": "L"},
    {"fifa_name": "Panama",              "iso3": "PAN", "iso2": "PA", "group": "L"},
]


# Build indexes once at import time; COUNTRY_MAP is immutable in spirit.
_BY_FIFA_NAME = {entry["fifa_name"]: entry["iso3"] for entry in COUNTRY_MAP}
_BY_ISO3 = {entry["iso3"]: entry for entry in COUNTRY_MAP}


def get_iso3(fifa_name: str) -> str:
    """Return the ISO-3 code for a FIFA-display name. Raises KeyError if unknown."""
    try:
        return _BY_FIFA_NAME[fifa_name]
    except KeyError:
        raise KeyError(f"Unknown FIFA name: {fifa_name!r}") from None


def get_fifa_name(iso3: str) -> str:
    """Return the FIFA-display name for an ISO-3 code. Raises KeyError if unknown."""
    try:
        return _BY_ISO3[iso3]["fifa_name"]
    except KeyError:
        raise KeyError(f"Unknown ISO3 code: {iso3!r}") from None


def get_group(iso3: str) -> str:
    """Return the group letter (A-L) for an ISO-3 code. Raises KeyError if unknown."""
    try:
        return _BY_ISO3[iso3]["group"]
    except KeyError:
        raise KeyError(f"Unknown ISO3 code: {iso3!r}") from None


def get_iso2(iso3: str) -> str:
    """Return the ISO-2 code for an ISO-3 code. Raises KeyError if unknown."""
    try:
        return _BY_ISO3[iso3]["iso2"]
    except KeyError:
        raise KeyError(f"Unknown ISO3 code: {iso3!r}") from None
