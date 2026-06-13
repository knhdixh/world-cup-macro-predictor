"""Bond Vigilantes World Cup economic model.

Implements the "Bond Vigilantes" inspired economic formula used to weight
national teams in the World Cup prediction pipeline. The model is a pure
product of six terms, each capturing one macroeconomic channel:

    score = max(log10(pop) - 6, 0) ** 1.2      # population scale
          * (1 + gdp / 8)                       # growth tailwind
          * 1 / (1 + infl / 8)                  # inflation drag
          * (1 - unemp)                         # employment drag
          * 1 / (1 + rate / 20)                 # interest-rate drag (vigilantes)
          * 1 / (0.8 + debt_gdp / 5)            # fiscal-space drag

The score is a dimensionless multiplier. Values > 1 indicate net
economic tailwind; values < 1 indicate net drag. For major economies the
score typically falls in roughly [0, 5]. Tiny nations (pop < 1M, e.g.
Curaçao) clamp to a population term of 0 and therefore receive an
overall score of 0, NOT NaN.

------------------------------------------------------------------------
UNIT CONVENTIONS (CRITICAL — these are not uniform across inputs!)
------------------------------------------------------------------------
  pop      : absolute number   (e.g., 330_000_000 for 330M)
  gdp      : PERCENTAGE form   (e.g., 3.5 for 3.5% growth, NOT 0.035)
  infl     : PERCENTAGE form   (e.g., 3.0 for 3.0% inflation, NOT 0.03)
  unemp    : DECIMAL form      (e.g., 0.04 for 4% unemployment, NOT 4.0)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
             NOTE: unemployment uses DECIMAL form. It is the ONE input
             expressed as a fraction, not a percentage. Don't change it.
  rate     : PERCENTAGE form   (e.g., 5.0 for 5.0% policy rate, NOT 0.05)
  debt_gdp : RATIO form        (e.g., 0.80 for 80% debt-to-GDP, NOT 80)
------------------------------------------------------------------------

No pandas / no external deps — pure Python math.
"""

import math

__all__ = ["compute_econ_score"]


def compute_econ_score(
    pop: float,
    gdp: float,
    infl: float,
    unemp: float,
    rate: float,
    debt_gdp: float,
) -> float:
    """Compute the Bond Vigilantes economic strength score.

    Parameters
    ----------
    pop : float
        Population in absolute count (e.g., 330_000_000).
    gdp : float
        Real GDP growth rate in percentage form (e.g., 2.5 for 2.5%).
    infl : float
        Inflation rate in percentage form (e.g., 3.0 for 3.0%).
    unemp : float
        Unemployment rate in DECIMAL form (e.g., 0.04 for 4%).
    rate : float
        Central-bank policy rate in percentage form (e.g., 5.0 for 5.0%).
    debt_gdp : float
        Government debt-to-GDP ratio in ratio form (e.g., 1.10 for 110%).

    Returns
    -------
    float
        The dimensionless economic score. Returns 0.0 for very small
        populations (the population term is clamped to 0 via max(..., 0)).
    """
    # --- Population term --------------------------------------------------
    # log10(pop) - 6  →  0 when pop = 1_000_000, grows with size.
    # Clamp at 0 so tiny countries (Curaçao, etc.) don't yield a negative
    # number; raising a clamped zero to 1.2 keeps it at 0, not NaN.
    pop_term = math.pow(max(math.log10(pop) - 6.0, 0.0), 1.2)

    # --- Growth tailwind --------------------------------------------------
    # (1 + gdp/8) — gdp in % form; gdp=8% gives a 2.0x multiplier.
    gdp_term = 1.0 + gdp / 8.0

    # --- Inflation drag ---------------------------------------------------
    # 1 / (1 + infl/8) — infl=8% halves the score; infl=40% cuts to ~0.167.
    infl_term = 1.0 / (1.0 + infl / 8.0)

    # --- Unemployment drag -----------------------------------------------
    # (1 - unemp) — unemp in DECIMAL form; unemp=0.04 leaves 0.96.
    unemp_term = 1.0 - unemp

    # --- Interest-rate drag (the "Bond Vigilantes" term) -----------------
    # 1 / (1 + rate/20) — rate=5% cuts to 0.8; rate=20% cuts to 0.5.
    rate_term = 1.0 / (1.0 + rate / 20.0)

    # --- Fiscal-space drag ------------------------------------------------
    # 1 / (0.8 + debt_gdp/5) — debt_gdp=0 gives 1.25 (some baseline slack);
    # debt_gdp=2.55 (Japan-ish) gives ~0.763; debt_gdp=4 gives ~0.5.
    debt_term = 1.0 / (0.8 + debt_gdp / 5.0)

    return pop_term * gdp_term * infl_term * unemp_term * rate_term * debt_term
