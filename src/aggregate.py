"""Aggregate data from multiple sources into a unified pandas DataFrame.

This module consumes already-fetched data (IMF, BIS, FIFA) and merges them
into a single DataFrame with normalized scores.  It does **not** call external
APIs and it does **not** re-apply unit conversions — the fetchers handle both.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

from src.formula import compute_econ_score

logger = logging.getLogger(__name__)

__all__ = ["build_dataset", "normalize_scores"]


def build_dataset(
    imf_data: Dict[str, dict],
    bis_rates: Dict[str, float | None],
    fifa_data: Dict[str, float],
    country_map: List[Dict[str, str]],
) -> pd.DataFrame:
    """Merge IMF, BIS and FIFA data into a single DataFrame.

    Parameters
    ----------
    imf_data : dict
        Output of ``fetch_imf_data()`` — keyed by ISO3, values contain
        ``pop``, ``gdp``, ``infl``, ``unemp``, ``debt_gdp``.
    bis_rates : dict
        Output of ``fetch_all_policy_rates()`` — keyed by ISO3, values are
        policy rates (percentage form) or ``None``.
    fifa_data : dict
        FIFA ranking points — keyed by ISO3.
    country_map : list[dict]
        List of country entries (e.g. ``COUNTRY_MAP``).  Each entry must
        contain the key ``"iso3"``.

    Returns
    -------
    pd.DataFrame
        Columns (in order):
        ``iso3``, ``pop``, ``gdp``, ``infl``, ``unemp``, ``rate``,
        ``debt_gdp``, ``fifa_points``, ``econ_score``.

    Notes
    -----
    * Missing BIS rates are filled with the median of available rates.
    * Missing values in other columns are replaced with conservative
      fallbacks so that rows are never dropped.
    * Warnings are logged for every missing or imputed value.
    """
    rows: list[dict[str, Any]] = []

    # Pre-compute median of available BIS rates once
    available_rates = [v for v in bis_rates.values() if v is not None]
    if available_rates:
        median_rate = float(pd.Series(available_rates).median())
    else:
        median_rate = 0.0
        logger.warning("No BIS rates available at all; using 0.0 as fallback")

    for entry in country_map:
        iso3 = entry["iso3"]
        imf = imf_data.get(iso3, {})

        pop = imf.get("pop")
        gdp = imf.get("gdp")
        infl = imf.get("infl")
        unemp = imf.get("unemp")
        debt_gdp = imf.get("debt_gdp")
        rate = bis_rates.get(iso3)
        fifa_points = fifa_data.get(iso3)

        # Log warnings and apply fallbacks for missing data
        if pop is None:
            logger.warning("Missing pop for %s; using 1.0 (score → 0)", iso3)
            pop = 1.0
        if gdp is None:
            logger.warning("Missing gdp for %s; using 0.0", iso3)
            gdp = 0.0
        if infl is None:
            logger.warning("Missing infl for %s; using 0.0", iso3)
            infl = 0.0
        if unemp is None:
            logger.warning("Missing unemp for %s; using 0.0", iso3)
            unemp = 0.0
        if debt_gdp is None:
            logger.warning("Missing debt_gdp for %s; using 0.0", iso3)
            debt_gdp = 0.0

        if rate is None:
            rate = median_rate
            logger.warning("Missing BIS rate for %s; filled with median %.2f", iso3, rate)

        if fifa_points is None:
            logger.warning("Missing fifa_points for %s; using 0.0", iso3)
            fifa_points = 0.0

        econ_score = compute_econ_score(pop, gdp, infl, unemp, rate, debt_gdp)

        rows.append(
            {
                "iso3": iso3,
                "pop": pop,
                "gdp": gdp,
                "infl": infl,
                "unemp": unemp,
                "rate": rate,
                "debt_gdp": debt_gdp,
                "fifa_points": fifa_points,
                "econ_score": econ_score,
            }
        )

    columns = [
        "iso3",
        "pop",
        "gdp",
        "infl",
        "unemp",
        "rate",
        "debt_gdp",
        "fifa_points",
        "econ_score",
    ]
    return pd.DataFrame(rows, columns=columns)


def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add min-max normalised FIFA and economic score columns.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame produced by :func:`build_dataset`.

    Returns
    -------
    pd.DataFrame
        Copy of *df* with two extra columns:
        ``norm_fifa`` and ``norm_econ``, each scaled to ``[0, 1]``.
    """
    df = df.copy()

    min_fifa = df["fifa_points"].min()
    max_fifa = df["fifa_points"].max()
    range_fifa = max_fifa - min_fifa
    if range_fifa == 0:
        df["norm_fifa"] = 1.0
    else:
        df["norm_fifa"] = (df["fifa_points"] - min_fifa) / range_fifa

    min_econ = df["econ_score"].min()
    max_econ = df["econ_score"].max()
    range_econ = max_econ - min_econ
    if range_econ == 0:
        df["norm_econ"] = 1.0
    else:
        df["norm_econ"] = (df["econ_score"] - min_econ) / range_econ

    return df
