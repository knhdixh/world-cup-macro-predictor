"""FIFA ranking data for the 48 World Cup 2026 nations.

Hardcoded FIFA men's ranking points as of April 1, 2026. Keys are
ISO 3166-1 alpha-3 country codes; values are FIFA ranking points (float).

Sources: FIFA/Coca-Cola Men's World Ranking, snapshot 2026-04-01.
Note: GBR is used as the key for England (the qualifying entity for
the World Cup 2026 European slots).
"""

from __future__ import annotations

FIFA_DATA: dict[str, float] = {
    "FRA": 1877.32,
    "ESP": 1876.40,
    "ARG": 1874.81,
    "GBR": 1825.97,
    "PRT": 1763.83,
    "BRA": 1761.16,
    "NLD": 1757.87,
    "MAR": 1755.87,
    "BEL": 1734.71,
    "DEU": 1730.37,
    "HRV": 1717.07,
    "COL": 1693.09,
    "SEN": 1688.99,
    "MEX": 1681.03,
    "USA": 1673.13,
    "URY": 1673.07,
    "JPN": 1660.43,
    "CHE": 1649.40,
    "IRN": 1615.30,
    "TUR": 1599.04,
    "ECU": 1594.78,
    "AUT": 1593.45,
    "KOR": 1588.66,
    "AUS": 1580.67,
    "DZA": 1564.26,
    "EGY": 1563.24,
    "CAN": 1556.48,
    "NOR": 1550.94,
    "PAN": 1540.64,
    "CIV": 1532.98,
    "SWE": 1514.77,
    "PRY": 1503.50,
    "CZE": 1501.38,
    "SCO": 1498.35,
    "TUN": 1479.04,
    "COD": 1478.35,
    "UZB": 1465.34,
    "QAT": 1454.96,
    "IRQ": 1447.14,
    "ZAF": 1429.73,
    "SAU": 1421.43,
    "JOR": 1391.45,
    "BIH": 1385.84,
    "CPV": 1366.13,
    "GHA": 1346.31,
    "CUW": 1294.65,
    "HTI": 1291.71,
    "NZL": 1281.57,
}


__all__ = ["FIFA_DATA"]
