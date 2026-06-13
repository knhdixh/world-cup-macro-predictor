"""TDD tests for src.country_map.

Written FIRST per TDD. The implementation in src/country_map.py must make
these pass. Run with: python -m pytest tests/test_country_map.py -v
or fallback (no pytest): python tests/test_country_map.py
"""

import sys
import types
from pathlib import Path

# Allow running this file directly (python tests/test_country_map.py)
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

    _pytest.raises = _raises
    _pytest.main = lambda argv=None: 0
    sys.modules["pytest"] = _pytest
    pytest = _pytest  # type: ignore

from src.country_map import (  # noqa: E402
    COUNTRY_MAP,
    get_fifa_name,
    get_group,
    get_iso2,
    get_iso3,
)


def test_count_48():
    """The tournament has exactly 48 qualified nations across 12 groups of 4."""
    assert len(COUNTRY_MAP) == 48


def test_iso3_format():
    """Every ISO-3 code must be exactly 3 uppercase ASCII letters."""
    iso3_re = __import__("re").compile(r"^[A-Z]{3}$")
    for entry in COUNTRY_MAP:
        assert "iso3" in entry, f"missing iso3 key in {entry}"
        assert iso3_re.match(entry["iso3"]), f"bad iso3: {entry['iso3']!r}"


def test_iso2_format():
    """Every ISO-2 code must be exactly 2 uppercase ASCII letters."""
    iso2_re = __import__("re").compile(r"^[A-Z]{2}$")
    for entry in COUNTRY_MAP:
        assert "iso2" in entry, f"missing iso2 key in {entry}"
        assert iso2_re.match(entry["iso2"]), f"bad iso2: {entry['iso2']!r}"


def test_roundtrip():
    """For every entry, get_iso3(name) -> get_fifa_name(code) returns the original name."""
    for entry in COUNTRY_MAP:
        code = get_iso3(entry["fifa_name"])
        assert code == entry["iso3"], (
            f"get_iso3({entry['fifa_name']!r}) returned {code!r}, "
            f"expected {entry['iso3']!r}"
        )
        name = get_fifa_name(entry["iso3"])
        assert name == entry["fifa_name"], (
            f"get_fifa_name({entry['iso3']!r}) returned {name!r}, "
            f"expected {entry['fifa_name']!r}"
        )


def test_all_groups():
    """All 12 groups A through L must be present, each with 4 teams."""
    groups = [entry["group"] for entry in COUNTRY_MAP]
    assert set(groups) == set("ABCDEFGHIJKL"), (
        f"missing or extra groups: {sorted(set(groups))}"
    )
    for letter in "ABCDEFGHIJKL":
        count = groups.count(letter)
        assert count == 4, f"group {letter} has {count} teams, expected 4"


def test_tricky_mappings():
    """The historically tricky FIFA-name -> ISO3 mappings must be correct."""
    cases = {
        "Korea Republic": "KOR",
        "Côte d'Ivoire": "CIV",
        "IR Iran": "IRN",
        "USA": "USA",
        "Türkiye": "TUR",
        "Curaçao": "CUW",
    }
    for fifa_name, expected_iso3 in cases.items():
        assert get_iso3(fifa_name) == expected_iso3, (
            f"get_iso3({fifa_name!r}) returned "
            f"{get_iso3(fifa_name)!r}, expected {expected_iso3!r}"
        )


def test_unknown_raises():
    """Unknown inputs must raise KeyError (no silent None)."""
    with pytest.raises(KeyError):
        get_iso3("Atlantis")
    with pytest.raises(KeyError):
        get_fifa_name("XXX")
    with pytest.raises(KeyError):
        get_group("XXX")
    with pytest.raises(KeyError):
        get_iso2("XXX")


def test_get_group_returns_letter():
    """get_group should return the group letter for a known ISO3."""
    for entry in COUNTRY_MAP:
        assert get_group(entry["iso3"]) == entry["group"]


def test_get_iso2_returns_correct_code():
    """get_iso2 should return the correct ISO-2 code for a known ISO3."""
    for entry in COUNTRY_MAP:
        assert get_iso2(entry["iso3"]) == entry["iso2"]


def test_iso2_tricky_mappings():
    """The historically tricky ISO3 -> ISO2 mappings must be correct."""
    cases = {
        "USA": "US",
        "KOR": "KR",
        "DEU": "DE",
        "CHE": "CH",
        "GBR": "GB",
        "SCO": "GB",
    }
    for iso3, expected_iso2 in cases.items():
        assert get_iso2(iso3) == expected_iso2, (
            f"get_iso2({iso3!r}) returned "
            f"{get_iso2(iso3)!r}, expected {expected_iso2!r}"
        )


if __name__ == "__main__":
    test_funcs = [
        test_count_48,
        test_iso3_format,
        test_iso2_format,
        test_roundtrip,
        test_all_groups,
        test_tricky_mappings,
        test_unknown_raises,
        test_get_group_returns_letter,
        test_get_iso2_returns_correct_code,
        test_iso2_tricky_mappings,
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
