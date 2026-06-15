"""Odds validation and team name resolution for the betting pipeline."""

from __future__ import annotations

from typing import Any
import unicodedata

from src.country_map import COUNTRY_MAP


def _normalize_team_name(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return "".join(ch.lower() for ch in folded if ch.isalnum())


TEAM_ALIASES: dict[str, str] = {}
for entry in COUNTRY_MAP:
    iso3 = entry["iso3"]
    fifa_name = entry["fifa_name"]
    TEAM_ALIASES[fifa_name] = iso3

    if fifa_name == "IR Iran":
        TEAM_ALIASES["Iran"] = iso3
        TEAM_ALIASES["Islamic Republic of Iran"] = iso3
    elif fifa_name == "Korea Republic":
        TEAM_ALIASES["South Korea"] = iso3
        TEAM_ALIASES["Republic of Korea"] = iso3
    elif fifa_name == "Côte d'Ivoire":
        TEAM_ALIASES["Ivory Coast"] = iso3
        TEAM_ALIASES["Cote d'Ivoire"] = iso3
        TEAM_ALIASES["Cote dIvoire"] = iso3
    elif fifa_name == "Cabo Verde":
        TEAM_ALIASES["Cape Verde"] = iso3
    elif fifa_name == "DR Congo":
        TEAM_ALIASES["Democratic Republic of the Congo"] = iso3
        TEAM_ALIASES["Congo DR"] = iso3
    elif fifa_name == "Türkiye":
        TEAM_ALIASES["Turkey"] = iso3
    elif fifa_name == "Curaçao":
        TEAM_ALIASES["Curacao"] = iso3
    elif fifa_name == "Czechia":
        TEAM_ALIASES["Czech Republic"] = iso3

# Reverse ISO3→FIFA so selection matching works in both directions
for entry in COUNTRY_MAP:
    iso3 = entry["iso3"]
    fifa_name = entry["fifa_name"]
    if iso3 not in TEAM_ALIASES:
        TEAM_ALIASES[iso3] = fifa_name

_NORMALIZED_TEAM_ALIASES = {_normalize_team_name(key): value for key, value in TEAM_ALIASES.items()}


def resolve_team_name(name: str) -> str:
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]

    normalized = _normalize_team_name(name)
    if normalized in _NORMALIZED_TEAM_ALIASES:
        return _NORMALIZED_TEAM_ALIASES[normalized]

    raise ValueError(f"Unrecognized team name: {name!r}")


def validate_odds_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fields = ("home", "away", "decimal_odds", "market", "selection")

    for field in required_fields:
        if field not in row or row[field] is None:
            errors.append(f"Missing required field: {field}")

    if "decimal_odds" in row and row.get("decimal_odds") is not None:
        try:
            decimal_odds = float(row["decimal_odds"])
        except (TypeError, ValueError):
            errors.append("decimal_odds must be a valid number greater than 1.01")
        else:
            if decimal_odds <= 1.01:
                errors.append("decimal_odds must be greater than 1.01")

    return errors


def validate_team_pair(home: str, away: str) -> tuple[str, str]:
    errors: list[str] = []

    try:
        home_iso3 = resolve_team_name(home)
    except ValueError as exc:
        errors.append(f"home team {home!r}: {exc}")
        home_iso3 = ""

    try:
        away_iso3 = resolve_team_name(away)
    except ValueError as exc:
        errors.append(f"away team {away!r}: {exc}")
        away_iso3 = ""

    if errors:
        raise ValueError("Unable to resolve team pair: " + "; ".join(errors))

    return home_iso3, away_iso3
