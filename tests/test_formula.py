"""TDD tests for src.formula (Bond Vigilantes World Cup economic model).

Written FIRST per TDD. The implementation in src/formula.py must make these
pass. Run with: python -m pytest tests/test_formula.py -v
or fallback (no pytest): python tests/test_formula.py

Formula under test:
    score = max(log10(pop) - 6, 0) ** 1.2
          * (1 + gdp / 8)
          * 1 / (1 + infl / 8)
          * (1 - unemp)
          * 1 / (1 + rate / 20)
          * 1 / (0.8 + debt_gdp / 5)

Unit conventions (CRITICAL — documented in src/formula.py):
    pop:      absolute number  (e.g., 330_000_000 for 330M)
    gdp:      percentage form   (e.g., 3.5 for 3.5%, NOT 0.035)
    infl:     percentage form   (e.g., 3.0 for 3.0%, NOT 0.03)
    unemp:    decimal form      (e.g., 0.04 for 4%, NOT 4.0)
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                    NOTE: unemp uses DECIMAL, not percentage!
    rate:     percentage form   (e.g., 5.0 for 5.0%, NOT 0.05)
    debt_gdp: ratio form        (e.g., 0.80 for 80%, NOT 80)
"""

import math
import sys
import types
from pathlib import Path

# Allow running this file directly (python tests/test_formula.py)
# by ensuring the project root is on sys.path.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    import pytest  # type: ignore
except ModuleNotFoundError:
    # Minimal stub so the tests can be run in environments without pytest
    # installed. When pytest IS available this branch is skipped and the
    # real pytest is used.
    _pytest = types.ModuleType("pytest")

    class _Raises:
        def __init__(self, exc):
            self.exc = exc

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(
                    f"DID NOT RAISE {self.exc.__name__}"
                )
            if not issubclass(exc_type, self.exc):
                return False
            # Suppress the exception — pytest.raises semantics.
            self._caught = exc_val
            return True

    def _raises(exc):
        return _Raises(exc)

    class _Approx:
        def __init__(self, expected, rel=None, abs=None):
            self.expected = expected
            self.rel = rel
            self.abs_tol = abs

        def __eq__(self, other):
            if self.abs_tol is not None:
                return abs(other - self.expected) <= self.abs_tol
            if self.rel is not None:
                return abs(other - self.expected) <= self.rel * abs(self.expected)
            return other == self.expected

    def _approx(expected, rel=1e-6, abs=None):
        return _Approx(expected, rel=rel, abs=abs)

    _pytest.raises = _raises
    _pytest.approx = _approx
    _pytest.main = lambda argv=None: 0
    sys.modules["pytest"] = _pytest
    pytest = _pytest  # type: ignore

from src.formula import compute_econ_score  # noqa: E402


# ---------------------------------------------------------------------------
# Anchor inputs used to "neutralize" most terms so we can isolate one term.
# pop=10_000_000 → log10(pop)=7 → (7-6)=1 → 1^1.2 = 1.0  (pop term = 1)
# gdp=0   → (1 + 0/8) = 1.0                              (gdp term = 1)
# unemp=0 → (1 - 0) = 1.0                                (unemp term = 1)
# rate=0  → 1/(1 + 0/20) = 1.0                           (rate term = 1)
# infl=0  → 1/(1 + 0/8) = 1.0                            (infl term = 1)
# debt_gdp=0 → 1/(0.8 + 0/5) = 1/0.8 = 1.25              (debt term = 1.25)
# ---------------------------------------------------------------------------
NEUTRAL_INPUTS = dict(
    pop=10_000_000,
    gdp=0,
    infl=0,
    unemp=0,
    rate=0,
    debt_gdp=0,
)


def _neutral(**overrides):
    """Return kwargs based on NEUTRAL_INPUTS with overrides applied."""
    merged = dict(NEUTRAL_INPUTS)
    merged.update(overrides)
    return merged


# ---------------------------------------------------------------------------
# 1. US manual calculation
# ---------------------------------------------------------------------------
def test_us_manual_calculation():
    """US economic inputs should yield a score of ~2.19 (within 0.1)."""
    s = compute_econ_score(
        pop=340_000_000,
        gdp=2.5,
        infl=3.0,
        unemp=0.04,
        rate=5.0,
        debt_gdp=1.10,
    )
    # Manual computation in the spec gives ≈ 2.1902.
    assert abs(s - 2.19) < 0.1, f"expected ~2.19, got {s}"


# ---------------------------------------------------------------------------
# 2. Curacao population clamp
# ---------------------------------------------------------------------------
def test_curacao_pop_clamp():
    """Curacao (pop≈150K) clamps the population term to 0; result is 0.0, not NaN."""
    s = compute_econ_score(
        pop=150_000,
        gdp=2.5,
        infl=3.0,
        unemp=0.04,
        rate=5.0,
        debt_gdp=1.10,
    )
    # log10(150_000) ≈ 5.176 → (5.176 - 6) = -0.824 → max(-0.824, 0) = 0
    # 0^1.2 = 0 → whole product = 0
    assert s == 0.0, f"expected 0.0, got {s}"
    assert not math.isnan(s), "result must not be NaN"
    assert not math.isinf(s), "result must not be Inf"


# ---------------------------------------------------------------------------
# 3. Qatar (severe GDP contraction) — gdp = -8.6
# ---------------------------------------------------------------------------
def test_qatar_negative_gdp():
    """Severe contraction (gdp=-8.6) must not crash; returns a finite real number."""
    s = compute_econ_score(
        pop=2_900_000,
        gdp=-8.6,
        infl=0,
        unemp=0,
        rate=0,
        debt_gdp=0,
    )
    # gdp_term = 1 + (-8.6)/8 = -0.075 → whole product is negative but real
    assert not math.isnan(s), "result must not be NaN"
    assert not math.isinf(s), "result must not be Inf"
    assert isinstance(s, float), f"expected float, got {type(s).__name__}"
    # The GDP term dominates: 1 + (-8.6)/8 = -0.075
    # The full product will be negative (one negative factor) but finite.
    assert s < 0, f"severe contraction should produce a negative result, got {s}"


# ---------------------------------------------------------------------------
# 4. Zero interest rate — rate term = 1/(1+0/20) = 1.0
# ---------------------------------------------------------------------------
def test_zero_rate():
    """rate=0 must yield rate term = 1.0 (no penalty)."""
    # Build a baseline with rate=0 vs same inputs with rate=5.
    base = compute_econ_score(**_neutral(rate=0.0))
    with_rate = compute_econ_score(**_neutral(rate=5.0))
    # base's rate term = 1.0; with_rate's rate term = 1/(1+5/20) = 1/1.25 = 0.8
    # So with_rate / base should equal 0.8 / 1.0 = 0.8
    assert base > 0, f"baseline should be positive, got {base}"
    ratio = with_rate / base
    assert abs(ratio - 0.8) < 1e-9, f"rate=5 should be 0.8x of rate=0, got {ratio}"


# ---------------------------------------------------------------------------
# 5. Hyperinflation (40%) — infl term = 1/(1+40/8) = 1/6 ≈ 0.167
# ---------------------------------------------------------------------------
def test_high_inflation():
    """infl=40 must produce the inflation term 1/(1+40/8) = 1/6 (heavy penalty)."""
    base = compute_econ_score(**_neutral(infl=0.0))
    hyper = compute_econ_score(**_neutral(infl=40.0))
    # base's infl term = 1.0; hyper's infl term = 1/6
    ratio = hyper / base
    assert abs(ratio - (1.0 / 6.0)) < 1e-9, (
        f"infl=40 should yield 1/6 of infl=0, got {ratio}"
    )
    # Sanity: 1/6 ≈ 0.1667
    assert abs((1.0 / 6.0) - 0.1667) < 0.001


# ---------------------------------------------------------------------------
# 6. Japan high debt (255%) — debt term = 1/(0.8+2.55/5) = 1/1.31 ≈ 0.763
# ---------------------------------------------------------------------------
def test_japan_high_debt():
    """debt_gdp=2.55 must produce the debt term 1/(0.8+2.55/5) = 1/1.31."""
    result = compute_econ_score(**_neutral(debt_gdp=2.55))
    # With neutral inputs, only the debt term varies from the neutral debt=0 case.
    neutral_result = compute_econ_score(**_neutral(debt_gdp=0.0))
    expected_debt_term = 1.0 / (0.8 + 2.55 / 5.0)  # = 1/1.31 ≈ 0.7634
    neutral_debt_term = 1.0 / (0.8 + 0.0 / 5.0)    # = 1/0.8 = 1.25
    # result / neutral_result should equal expected_debt_term / neutral_debt_term
    actual_ratio = result / neutral_result
    expected_ratio = expected_debt_term / neutral_debt_term
    assert abs(actual_ratio - expected_ratio) < 1e-9, (
        f"debt term ratio mismatch: got {actual_ratio}, expected {expected_ratio}"
    )
    # Sanity: 1/1.31 ≈ 0.763
    assert abs(expected_debt_term - 0.763) < 0.005


# ---------------------------------------------------------------------------
# 7. France vs New Zealand — economically larger France should score higher
# ---------------------------------------------------------------------------
def test_france_vs_nz():
    """France (68M, larger economy) should score significantly higher than NZ (5.1M)."""
    france = compute_econ_score(
        pop=68_000_000,
        gdp=1.2,
        infl=1.5,
        unemp=0.075,
        rate=2.5,
        debt_gdp=1.12,
    )
    nz = compute_econ_score(
        pop=5_100_000,
        gdp=1.0,
        infl=3.0,
        unemp=0.04,
        rate=5.5,
        debt_gdp=0.45,
    )
    assert france > nz, (
        f"France ({france:.4f}) should score higher than NZ ({nz:.4f})"
    )
    # Population dominates: France's pop_term ~1.7x NZ's pop_term.
    # All other terms combined still leave France ahead.
    assert france > 1.5 * nz, (
        f"France should be at least 1.5x NZ: france={france:.4f}, nz={nz:.4f}"
    )


# ---------------------------------------------------------------------------
# 8. No NaN / Inf across realistic edge cases
# ---------------------------------------------------------------------------
def test_no_nan():
    """A representative sweep of inputs must always return finite real numbers."""
    test_cases = [
        # (pop, gdp, infl, unemp, rate, debt_gdp)
        (340_000_000, 2.5, 3.0, 0.04, 5.0, 1.10),   # US
        (150_000, 2.5, 3.0, 0.04, 5.0, 1.10),        # Curacao (clamp)
        (2_900_000, -8.6, 0.0, 0.0, 0.0, 0.0),       # Qatar (negative gdp)
        (1_000_000, 0.0, 0.0, 0.0, 0.0, 0.0),        # tiny neutral
        (10_000_000, 1.0, 2.0, 0.05, 3.0, 0.8),      # mid-size typical
        (1_400_000_000, 5.0, 10.0, 0.1, 8.0, 2.0),   # China-sized, stressed
        (50_000_000, -2.0, 0.0, 0.05, 1.0, 0.5),     # negative growth
        (5_000_000, 3.0, 40.0, 0.15, 25.0, 5.0),     # extreme stress
    ]
    for i, (pop, gdp, infl, unemp, rate, debt_gdp) in enumerate(test_cases):
        s = compute_econ_score(pop, gdp, infl, unemp, rate, debt_gdp)
        assert isinstance(s, float), (
            f"case {i}: expected float, got {type(s).__name__}"
        )
        assert not math.isnan(s), f"case {i}: got NaN for {test_cases[i]}"
        assert not math.isinf(s), f"case {i}: got Inf for {test_cases[i]}"


# ---------------------------------------------------------------------------
# 9. (bonus) Return type contract
# ---------------------------------------------------------------------------
def test_returns_float():
    """compute_econ_score must always return a Python float."""
    s = compute_econ_score(50_000_000, 1.0, 2.0, 0.05, 3.0, 0.8)
    assert isinstance(s, float), f"expected float, got {type(s).__name__}"


# ---------------------------------------------------------------------------
# 10. (bonus) Manual component-by-component check on US case
# ---------------------------------------------------------------------------
def test_us_components_match_formula():
    """Verify each US term matches the formula spec, then check the product."""
    pop, gdp, infl, unemp, rate, debt_gdp = 340_000_000, 2.5, 3.0, 0.04, 5.0, 1.10
    expected_pop = math.pow(max(math.log10(pop) - 6.0, 0.0), 1.2)
    expected_gdp = 1.0 + gdp / 8.0
    expected_infl = 1.0 / (1.0 + infl / 8.0)
    expected_unemp = 1.0 - unemp
    expected_rate = 1.0 / (1.0 + rate / 20.0)
    expected_debt = 1.0 / (0.8 + debt_gdp / 5.0)
    expected = (
        expected_pop
        * expected_gdp
        * expected_infl
        * expected_unemp
        * expected_rate
        * expected_debt
    )
    actual = compute_econ_score(pop, gdp, infl, unemp, rate, debt_gdp)
    assert abs(actual - expected) < 1e-9, (
        f"score {actual} != component product {expected}"
    )


if __name__ == "__main__":
    test_funcs = [
        test_us_manual_calculation,
        test_curacao_pop_clamp,
        test_qatar_negative_gdp,
        test_zero_rate,
        test_high_inflation,
        test_japan_high_debt,
        test_france_vs_nz,
        test_no_nan,
        test_returns_float,
        test_us_components_match_formula,
    ]
    failures = 0
    for fn in test_funcs:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
        else:
            print(f"PASS {fn.__name__}")
    if failures:
        print(f"\n{failures} test(s) failed")
        sys.exit(1)
    print(f"\nAll {len(test_funcs)} tests passed")
