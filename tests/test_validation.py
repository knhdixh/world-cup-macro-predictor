"""TDD tests for src.validation.

Written FIRST per TDD. The implementation in src/validation.py must make
these pass. Run with: python -m pytest tests/test_validation.py -v
or fallback (no pytest): python tests/test_validation.py
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

# Allow running this file directly (python tests/test_validation.py)
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

    def _raises(exc):
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
                return True

        return _Raises(exc)

    _pytest.raises = _raises
    _pytest.main = lambda argv=None: 0
    _pytest.skip = lambda *a, **kw: None
    sys.modules["pytest"] = _pytest
    pytest = _pytest  # type: ignore

from src.validation import (  # noqa: E402
    EconData,
    check_all_nations_present,
    validate_econ_data,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_usa() -> EconData:
    """A perfectly valid USA economic profile."""
    return EconData(
        iso3="USA",
        pop=335_000_000,
        gdp=2.5,        # 2.5% GDP growth
        infl=3.0,        # 3.0% inflation
        unemp=0.04,      # 4% unemployment
        rate=5.0,        # 5% interest rate
        debt_gdp=1.25,   # 125% debt/GDP
        source="World Bank 2024",
    )


def _make_all_48() -> list[EconData]:
    """Build one EconData for every nation in COUNTRY_MAP.

    The data values are intentionally generic-but-valid so this helper
    can be used as a happy-path baseline.
    """
    from src.country_map import COUNTRY_MAP
    out: list[EconData] = []
    for entry in COUNTRY_MAP:
        out.append(
            EconData(
                iso3=entry["iso3"],
                pop=10_000_000,
                gdp=2.0,
                infl=3.0,
                unemp=0.05,
                rate=3.0,
                debt_gdp=0.6,
                source="World Bank 2024",
            )
        )
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_valid_data_passes():
    """A perfectly valid USA record should pass with zero warnings."""
    data = [_make_usa()]
    validated, warnings = validate_econ_data(data)
    assert validated == data, "valid data should be returned unchanged"
    assert warnings == [], f"expected no warnings, got {warnings!r}"


def test_missing_nation():
    """47 nations instead of 48 must emit a warning but still return the data."""
    data = _make_all_48()[:47]  # drop the last nation
    assert len(data) == 47, "test precondition: must start with 47 records"
    validated, range_warnings = validate_econ_data(data)
    completeness_warnings = check_all_nations_present(data)
    warnings = range_warnings + completeness_warnings
    assert validated == data, "data should be returned even when nations are missing"
    assert any("missing" in w.lower() or "48" in w or "47" in w for w in warnings), (
        f"expected a missing-nation warning, got {warnings!r}"
    )


def test_extreme_but_valid():
    """Turkey-style 40% inflation is unusual but inside the allowed range."""
    data = [
        EconData(
            iso3="TUR",
            pop=85_000_000,
            gdp=3.0,
            infl=40.0,        # high but <= 200
            unemp=0.10,
            rate=25.0,
            debt_gdp=0.50,
            source="World Bank 2024",
        )
    ]
    validated, warnings = validate_econ_data(data)
    assert validated == data, "extreme-but-valid data should pass through"
    assert warnings == [], (
        f"40% inflation is within the valid range and should NOT warn, got {warnings!r}"
    )


def test_impossible_value():
    """Negative unemployment (-0.1) is impossible and must trigger a warning."""
    data = [
        EconData(
            iso3="USA",
            pop=335_000_000,
            gdp=2.5,
            infl=3.0,
            unemp=-0.1,        # impossible: unemployment cannot be negative
            rate=5.0,
            debt_gdp=1.25,
            source="World Bank 2024",
        )
    ]
    validated, warnings = validate_econ_data(data)
    # The data must still be returned — warnings are non-fatal.
    assert validated == data, "data should be returned even with a warning"
    assert len(warnings) >= 1, "expected at least one warning for unemp=-0.1"
    assert any("unemp" in w.lower() or "USA" in w for w in warnings), (
        f"expected an unemp/USA warning, got {warnings!r}"
    )


def test_48_nations_validated():
    """All 48 ISO3 codes from COUNTRY_MAP should pass when fed valid data."""
    try:
        from src.country_map import COUNTRY_MAP  # noqa: F401
    except Exception:  # pragma: no cover - guard for the "skip if not available" rule
        pytest.skip("country_map not available")
    data = _make_all_48()
    assert len(data) == 48, "test precondition: must have 48 records"
    validated, range_warnings = validate_econ_data(data)
    completeness_warnings = check_all_nations_present(data)
    warnings = range_warnings + completeness_warnings
    assert len(validated) == 48, "all 48 records should pass through"
    assert warnings == [], (
        f"all-valid 48-nation dataset should not warn, got {warnings!r}"
    )


def test_curacao_small_pop():
    """Curacao's ~150K population is small but valid — must NOT warn or NaN."""
    data = [
        EconData(
            iso3="CUW",
            pop=150_000,       # Curaçao's real population
            gdp=2.0,
            infl=3.0,
            unemp=0.07,
            rate=3.0,
            debt_gdp=0.40,
            source="World Bank 2024",
        )
    ]
    validated, warnings = validate_econ_data(data)
    assert validated == data, "small-but-valid Curacao record should pass through"
    assert warnings == [], (
        f"Curaçao (pop=150K) is within the valid range and should NOT warn, "
        f"got {warnings!r}"
    )
    # Explicit NaN check — must not have been silently coerced to NaN.
    assert validated[0].pop == 150_000, "pop must NOT be NaN after validation"


# ---------------------------------------------------------------------------
# Bonus tests (kept small but increase coverage)
# ---------------------------------------------------------------------------

def test_none_value_warns():
    """A None for a required field must produce a warning, not a crash."""
    data = [
        EconData(
            iso3="BRA",
            pop=None,            # type: ignore[arg-type]
            gdp=1.5,
            infl=4.0,
            unemp=0.08,
            rate=10.0,
            debt_gdp=0.85,
            source="World Bank 2024",
        )
    ]
    validated, warnings = validate_econ_data(data)
    assert validated == data, "data should be returned even with a None"
    assert any("BRA" in w or "pop" in w.lower() or "none" in w.lower() for w in warnings), (
        f"expected a None/missing warning, got {warnings!r}"
    )


def test_return_types():
    """validate_econ_data must return a (list, list) tuple."""
    validated, warnings = validate_econ_data([_make_usa()])
    assert isinstance(validated, list)
    assert isinstance(warnings, list)


def test_econ_data_is_dataclass_or_struct():
    """EconData should expose the documented field names."""
    if hasattr(EconData, "__dataclass_fields__"):
        fields = set(EconData.__dataclass_fields__.keys())
    else:
        fields = {f for f in dir(EconData) if not f.startswith("_")}
    required = {"iso3", "pop", "gdp", "infl", "unemp", "rate", "debt_gdp", "source"}
    missing = required - fields
    assert not missing, f"EconData missing required fields: {missing}"


def test_japan_extreme_debt():
    """Japan's debt/GDP ~2.55 (255%) is the upper bound of realistic values."""
    data = [
        EconData(
            iso3="JPN",
            pop=125_000_000,
            gdp=1.0,
            infl=2.0,
            unemp=0.025,
            rate=0.1,
            debt_gdp=2.55,    # 255% — extreme but real
            source="World Bank 2024",
        )
    ]
    validated, warnings = validate_econ_data(data)
    assert validated == data, "Japan's 255% debt should pass"
    assert warnings == [], (
        f"debt_gdp=2.55 is within the valid range and should NOT warn, "
        f"got {warnings!r}"
    )


if __name__ == "__main__":
    test_funcs = [
        test_valid_data_passes,
        test_missing_nation,
        test_extreme_but_valid,
        test_impossible_value,
        test_48_nations_validated,
        test_curacao_small_pop,
        test_none_value_warns,
        test_return_types,
        test_econ_data_is_dataclass_or_struct,
        test_japan_extreme_debt,
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
