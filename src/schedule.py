"""World Cup 2026 match schedule.

Contains all 104 matches (72 group-stage + 32 knockout) as a list of dicts.
Each match has:
    match_number (int): 1..104
    group        (str | None): "A".."L" for group, None for knockout
    date         (str): ISO "YYYY-MM-DD"
    team_a       (str): FIFA name
    team_b       (str): FIFA name
    matchday     (int | None): 1, 2, or 3 for group; None for knockout
    status       (str): "played" | "today" | "upcoming" | "knockout"

Knockout pairings are placeholders (e.g. "1A vs 3rd" denotes Winner Group A
versus a best-3rd-place team) and will be resolved once group results are
known.
"""

from __future__ import annotations

from datetime import date
from typing import Any


# ---------------------------------------------------------------------------
# Group-stage matches (#1 - #72)
# ---------------------------------------------------------------------------

_GROUP_MATCHES: list[dict[str, Any]] = [
    # Matchday 1 (Jun 11 - Jun 17) ----------------------------------------
    {"match_number": 1,  "group": "A", "date": "2026-06-11", "team_a": "Mexico",                "team_b": "South Africa",          "matchday": 1, "status": "played"},
    {"match_number": 2,  "group": "A", "date": "2026-06-11", "team_a": "Korea Republic",        "team_b": "Czechia",               "matchday": 1, "status": "played"},
    {"match_number": 3,  "group": "B", "date": "2026-06-12", "team_a": "Canada",                "team_b": "Bosnia and Herzegovina", "matchday": 1, "status": "played"},
    {"match_number": 4,  "group": "D", "date": "2026-06-12", "team_a": "USA",                   "team_b": "Paraguay",              "matchday": 1, "status": "played"},
    {"match_number": 5,  "group": "B", "date": "2026-06-13", "team_a": "Qatar",                 "team_b": "Switzerland",           "matchday": 1, "status": "today"},
    {"match_number": 6,  "group": "C", "date": "2026-06-13", "team_a": "Brazil",                "team_b": "Morocco",               "matchday": 1, "status": "today"},
    {"match_number": 7,  "group": "C", "date": "2026-06-13", "team_a": "Haiti",                 "team_b": "Scotland",              "matchday": 1, "status": "today"},
    {"match_number": 8,  "group": "D", "date": "2026-06-13", "team_a": "Australia",             "team_b": "Türkiye",               "matchday": 1, "status": "today"},
    {"match_number": 9,  "group": "E", "date": "2026-06-14", "team_a": "Germany",               "team_b": "Curaçao",               "matchday": 1, "status": "upcoming"},
    {"match_number": 10, "group": "F", "date": "2026-06-14", "team_a": "Netherlands",           "team_b": "Japan",                 "matchday": 1, "status": "upcoming"},
    {"match_number": 11, "group": "E", "date": "2026-06-14", "team_a": "Côte d'Ivoire",         "team_b": "Ecuador",               "matchday": 1, "status": "upcoming"},
    {"match_number": 12, "group": "F", "date": "2026-06-14", "team_a": "Sweden",                "team_b": "Tunisia",               "matchday": 1, "status": "upcoming"},
    {"match_number": 13, "group": "H", "date": "2026-06-15", "team_a": "Spain",                 "team_b": "Cabo Verde",            "matchday": 1, "status": "upcoming"},
    {"match_number": 14, "group": "G", "date": "2026-06-15", "team_a": "Belgium",               "team_b": "Egypt",                 "matchday": 1, "status": "upcoming"},
    {"match_number": 15, "group": "H", "date": "2026-06-15", "team_a": "Saudi Arabia",          "team_b": "Uruguay",               "matchday": 1, "status": "upcoming"},
    {"match_number": 16, "group": "G", "date": "2026-06-15", "team_a": "IR Iran",               "team_b": "New Zealand",           "matchday": 1, "status": "upcoming"},
    {"match_number": 17, "group": "I", "date": "2026-06-16", "team_a": "France",                "team_b": "Senegal",               "matchday": 1, "status": "upcoming"},
    {"match_number": 18, "group": "I", "date": "2026-06-16", "team_a": "Iraq",                  "team_b": "Norway",                "matchday": 1, "status": "upcoming"},
    {"match_number": 19, "group": "J", "date": "2026-06-16", "team_a": "Argentina",             "team_b": "Algeria",               "matchday": 1, "status": "upcoming"},
    {"match_number": 20, "group": "J", "date": "2026-06-16", "team_a": "Austria",               "team_b": "Jordan",                "matchday": 1, "status": "upcoming"},
    {"match_number": 21, "group": "K", "date": "2026-06-17", "team_a": "Portugal",              "team_b": "DR Congo",              "matchday": 1, "status": "upcoming"},
    {"match_number": 22, "group": "L", "date": "2026-06-17", "team_a": "England",               "team_b": "Croatia",               "matchday": 1, "status": "upcoming"},
    {"match_number": 23, "group": "L", "date": "2026-06-17", "team_a": "Ghana",                 "team_b": "Panama",                "matchday": 1, "status": "upcoming"},
    {"match_number": 24, "group": "K", "date": "2026-06-17", "team_a": "Uzbekistan",            "team_b": "Colombia",              "matchday": 1, "status": "upcoming"},
    # Matchday 2 (Jun 18 - Jun 23) ----------------------------------------
    {"match_number": 25, "group": "A", "date": "2026-06-18", "team_a": "Czechia",               "team_b": "South Africa",          "matchday": 2, "status": "upcoming"},
    {"match_number": 26, "group": "B", "date": "2026-06-18", "team_a": "Switzerland",           "team_b": "Bosnia and Herzegovina", "matchday": 2, "status": "upcoming"},
    {"match_number": 27, "group": "B", "date": "2026-06-18", "team_a": "Canada",                "team_b": "Qatar",                 "matchday": 2, "status": "upcoming"},
    {"match_number": 28, "group": "A", "date": "2026-06-18", "team_a": "Mexico",                "team_b": "Korea Republic",        "matchday": 2, "status": "upcoming"},
    {"match_number": 29, "group": "D", "date": "2026-06-19", "team_a": "USA",                   "team_b": "Australia",             "matchday": 2, "status": "upcoming"},
    {"match_number": 30, "group": "C", "date": "2026-06-19", "team_a": "Scotland",              "team_b": "Morocco",               "matchday": 2, "status": "upcoming"},
    {"match_number": 31, "group": "C", "date": "2026-06-19", "team_a": "Brazil",                "team_b": "Haiti",                 "matchday": 2, "status": "upcoming"},
    {"match_number": 32, "group": "D", "date": "2026-06-19", "team_a": "Türkiye",               "team_b": "Paraguay",              "matchday": 2, "status": "upcoming"},
    {"match_number": 33, "group": "F", "date": "2026-06-20", "team_a": "Netherlands",           "team_b": "Sweden",                "matchday": 2, "status": "upcoming"},
    {"match_number": 34, "group": "E", "date": "2026-06-20", "team_a": "Germany",               "team_b": "Côte d'Ivoire",         "matchday": 2, "status": "upcoming"},
    {"match_number": 35, "group": "E", "date": "2026-06-20", "team_a": "Ecuador",               "team_b": "Curaçao",               "matchday": 2, "status": "upcoming"},
    {"match_number": 36, "group": "F", "date": "2026-06-20", "team_a": "Tunisia",               "team_b": "Japan",                 "matchday": 2, "status": "upcoming"},
    {"match_number": 37, "group": "H", "date": "2026-06-21", "team_a": "Spain",                 "team_b": "Saudi Arabia",          "matchday": 2, "status": "upcoming"},
    {"match_number": 38, "group": "G", "date": "2026-06-21", "team_a": "Belgium",               "team_b": "IR Iran",               "matchday": 2, "status": "upcoming"},
    {"match_number": 39, "group": "H", "date": "2026-06-21", "team_a": "Uruguay",               "team_b": "Cabo Verde",            "matchday": 2, "status": "upcoming"},
    {"match_number": 40, "group": "G", "date": "2026-06-21", "team_a": "New Zealand",           "team_b": "Egypt",                 "matchday": 2, "status": "upcoming"},
    {"match_number": 41, "group": "J", "date": "2026-06-22", "team_a": "Argentina",             "team_b": "Austria",               "matchday": 2, "status": "upcoming"},
    {"match_number": 42, "group": "I", "date": "2026-06-22", "team_a": "France",                "team_b": "Iraq",                  "matchday": 2, "status": "upcoming"},
    {"match_number": 43, "group": "I", "date": "2026-06-22", "team_a": "Norway",                "team_b": "Senegal",               "matchday": 2, "status": "upcoming"},
    {"match_number": 44, "group": "J", "date": "2026-06-22", "team_a": "Jordan",                "team_b": "Algeria",               "matchday": 2, "status": "upcoming"},
    {"match_number": 45, "group": "K", "date": "2026-06-23", "team_a": "Portugal",              "team_b": "Uzbekistan",            "matchday": 2, "status": "upcoming"},
    {"match_number": 46, "group": "L", "date": "2026-06-23", "team_a": "England",               "team_b": "Ghana",                 "matchday": 2, "status": "upcoming"},
    {"match_number": 47, "group": "L", "date": "2026-06-23", "team_a": "Panama",                "team_b": "Croatia",               "matchday": 2, "status": "upcoming"},
    {"match_number": 48, "group": "K", "date": "2026-06-23", "team_a": "Colombia",              "team_b": "DR Congo",              "matchday": 2, "status": "upcoming"},
    # Matchday 3 (Jun 24 - Jun 27) ----------------------------------------
    {"match_number": 49, "group": "B", "date": "2026-06-24", "team_a": "Switzerland",           "team_b": "Canada",                "matchday": 3, "status": "upcoming"},
    {"match_number": 50, "group": "B", "date": "2026-06-24", "team_a": "Bosnia and Herzegovina", "team_b": "Qatar",                "matchday": 3, "status": "upcoming"},
    {"match_number": 51, "group": "C", "date": "2026-06-24", "team_a": "Scotland",              "team_b": "Brazil",                "matchday": 3, "status": "upcoming"},
    {"match_number": 52, "group": "C", "date": "2026-06-24", "team_a": "Morocco",               "team_b": "Haiti",                 "matchday": 3, "status": "upcoming"},
    {"match_number": 53, "group": "A", "date": "2026-06-24", "team_a": "Czechia",               "team_b": "Mexico",                "matchday": 3, "status": "upcoming"},
    {"match_number": 54, "group": "A", "date": "2026-06-24", "team_a": "South Africa",          "team_b": "Korea Republic",        "matchday": 3, "status": "upcoming"},
    {"match_number": 55, "group": "E", "date": "2026-06-25", "team_a": "Ecuador",               "team_b": "Germany",               "matchday": 3, "status": "upcoming"},
    {"match_number": 56, "group": "E", "date": "2026-06-25", "team_a": "Curaçao",               "team_b": "Côte d'Ivoire",         "matchday": 3, "status": "upcoming"},
    {"match_number": 57, "group": "F", "date": "2026-06-25", "team_a": "Japan",                 "team_b": "Sweden",                "matchday": 3, "status": "upcoming"},
    {"match_number": 58, "group": "F", "date": "2026-06-25", "team_a": "Tunisia",               "team_b": "Netherlands",           "matchday": 3, "status": "upcoming"},
    {"match_number": 59, "group": "D", "date": "2026-06-25", "team_a": "Türkiye",               "team_b": "USA",                   "matchday": 3, "status": "upcoming"},
    {"match_number": 60, "group": "D", "date": "2026-06-25", "team_a": "Paraguay",              "team_b": "Australia",             "matchday": 3, "status": "upcoming"},
    {"match_number": 61, "group": "I", "date": "2026-06-26", "team_a": "Senegal",               "team_b": "Iraq",                  "matchday": 3, "status": "upcoming"},
    {"match_number": 62, "group": "I", "date": "2026-06-26", "team_a": "Norway",                "team_b": "France",                "matchday": 3, "status": "upcoming"},
    {"match_number": 63, "group": "H", "date": "2026-06-26", "team_a": "Cabo Verde",            "team_b": "Saudi Arabia",          "matchday": 3, "status": "upcoming"},
    {"match_number": 64, "group": "H", "date": "2026-06-26", "team_a": "Uruguay",               "team_b": "Spain",                 "matchday": 3, "status": "upcoming"},
    {"match_number": 65, "group": "G", "date": "2026-06-26", "team_a": "Egypt",                 "team_b": "IR Iran",               "matchday": 3, "status": "upcoming"},
    {"match_number": 66, "group": "G", "date": "2026-06-26", "team_a": "New Zealand",           "team_b": "Belgium",               "matchday": 3, "status": "upcoming"},
    {"match_number": 67, "group": "L", "date": "2026-06-27", "team_a": "Croatia",               "team_b": "Ghana",                 "matchday": 3, "status": "upcoming"},
    {"match_number": 68, "group": "L", "date": "2026-06-27", "team_a": "Panama",                "team_b": "England",               "matchday": 3, "status": "upcoming"},
    {"match_number": 69, "group": "K", "date": "2026-06-27", "team_a": "Colombia",              "team_b": "Portugal",              "matchday": 3, "status": "upcoming"},
    {"match_number": 70, "group": "K", "date": "2026-06-27", "team_a": "DR Congo",              "team_b": "Uzbekistan",            "matchday": 3, "status": "upcoming"},
    {"match_number": 71, "group": "J", "date": "2026-06-27", "team_a": "Algeria",               "team_b": "Austria",               "matchday": 3, "status": "upcoming"},
    {"match_number": 72, "group": "J", "date": "2026-06-27", "team_a": "Jordan",                "team_b": "Argentina",             "matchday": 3, "status": "upcoming"},
]


# ---------------------------------------------------------------------------
# Knockout matches (#73 - #104) — placeholders
# ---------------------------------------------------------------------------
#
# 2026 format: 12 groups of 4 -> top 2 (24) + 8 best 3rd-place teams = 32.
# Knockout structure: 16 R32 + 8 R16 + 4 QF + 2 SF + 1 3rd-place + 1 Final = 32.
# Pairings below use official bracket placeholders ("1A" = winner of group A,
# "3rd" = one of the eight best 3rd-placed teams). They will be resolved
# once group results are known.

_KNOCKOUT_MATCHES: list[dict[str, Any]] = [
    # Round of 32 (Jun 28 - Jul 3) — 16 matches
    {"match_number": 73,  "date": "2026-06-28", "team_a": "1A", "team_b": "3rd"},
    {"match_number": 74,  "date": "2026-06-28", "team_a": "1C", "team_b": "3rd"},
    {"match_number": 75,  "date": "2026-06-29", "team_a": "1B", "team_b": "3rd"},
    {"match_number": 76,  "date": "2026-06-29", "team_a": "1D", "team_b": "3rd"},
    {"match_number": 77,  "date": "2026-06-30", "team_a": "1E", "team_b": "3rd"},
    {"match_number": 78,  "date": "2026-06-30", "team_a": "1F", "team_b": "3rd"},
    {"match_number": 79,  "date": "2026-07-01", "team_a": "1G", "team_b": "3rd"},
    {"match_number": 80,  "date": "2026-07-01", "team_a": "1H", "team_b": "3rd"},
    {"match_number": 81,  "date": "2026-07-02", "team_a": "1I", "team_b": "3rd"},
    {"match_number": 82,  "date": "2026-07-02", "team_a": "1J", "team_b": "3rd"},
    {"match_number": 83,  "date": "2026-07-03", "team_a": "1K", "team_b": "3rd"},
    {"match_number": 84,  "date": "2026-07-03", "team_a": "1L", "team_b": "3rd"},
    {"match_number": 85,  "date": "2026-07-03", "team_a": "2A", "team_b": "2B"},
    {"match_number": 86,  "date": "2026-07-03", "team_a": "2C", "team_b": "2D"},
    {"match_number": 87,  "date": "2026-07-02", "team_a": "2E", "team_b": "2F"},
    {"match_number": 88,  "date": "2026-07-02", "team_a": "2G", "team_b": "2H"},
    # Round of 16 (Jul 4 - Jul 7) — 8 matches
    {"match_number": 89,  "date": "2026-07-04", "team_a": "W73", "team_b": "W75"},
    {"match_number": 90,  "date": "2026-07-04", "team_a": "W74", "team_b": "W77"},
    {"match_number": 91,  "date": "2026-07-05", "team_a": "W76", "team_b": "W78"},
    {"match_number": 92,  "date": "2026-07-05", "team_a": "W79", "team_b": "W80"},
    {"match_number": 93,  "date": "2026-07-06", "team_a": "W81", "team_b": "W82"},
    {"match_number": 94,  "date": "2026-07-06", "team_a": "W83", "team_b": "W84"},
    {"match_number": 95,  "date": "2026-07-07", "team_a": "W85", "team_b": "W88"},
    {"match_number": 96,  "date": "2026-07-07", "team_a": "W86", "team_b": "W87"},
    # Quarter-finals (Jul 9 - Jul 11) — 4 matches
    {"match_number": 97,  "date": "2026-07-09",  "team_a": "W89", "team_b": "W90"},
    {"match_number": 98,  "date": "2026-07-10",  "team_a": "W91", "team_b": "W92"},
    {"match_number": 99,  "date": "2026-07-11",  "team_a": "W93", "team_b": "W94"},
    {"match_number": 100, "date": "2026-07-11",  "team_a": "W95", "team_b": "W96"},
    # Semi-finals (Jul 14 - Jul 15) — 2 matches
    {"match_number": 101, "date": "2026-07-14", "team_a": "W97", "team_b": "W98"},
    {"match_number": 102, "date": "2026-07-15", "team_a": "W99", "team_b": "W100"},
    # Third-place playoff (Jul 18)
    {"match_number": 103, "date": "2026-07-18", "team_a": "L101", "team_b": "L102"},
    # Final (Jul 19)
    {"match_number": 104, "date": "2026-07-19", "team_a": "W101", "team_b": "W102"},
]


def _build_matches() -> list[dict[str, Any]]:
    """Compose the full 104-match schedule, tagging knockout entries."""
    matches: list[dict[str, Any]] = []
    matches.extend(_GROUP_MATCHES)
    for ko in _KNOCKOUT_MATCHES:
        matches.append(
            {
                "match_number": ko["match_number"],
                "group": None,
                "date": ko["date"],
                "team_a": ko["team_a"],
                "team_b": ko["team_b"],
                "matchday": None,
                "status": "knockout",
            }
        )
    return matches


MATCHES: list[dict[str, Any]] = _build_matches()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_upcoming_matches(cutoff_date: str) -> list[dict[str, Any]]:
    """Return matches still upcoming as of ``cutoff_date`` (ISO ``YYYY-MM-DD``).

    Semantics:
        - ``cutoff_date`` represents "today".
        - Matches with status ``"played"`` are excluded (already finished).
        - Matches with status ``"today"`` are excluded (happening right now,
          so not "upcoming" yet).
        - Matches with status ``"upcoming"`` or ``"knockout"`` whose
          ``date >= cutoff_date`` are returned.

    The returned list preserves the original order of :data:`MATCHES`
    (i.e. sorted by ``match_number``).

    Parameters
    ----------
    cutoff_date:
        ISO date string ``YYYY-MM-DD``.

    Returns
    -------
    list[dict]
        Subset of :data:`MATCHES` that are not yet played as of the cutoff.
    """
    cutoff = date.fromisoformat(cutoff_date)
    return [
        m for m in MATCHES
        if m["status"] in ("upcoming", "knockout")
        and date.fromisoformat(m["date"]) >= cutoff
    ]


__all__ = ["MATCHES", "get_upcoming_matches"]
