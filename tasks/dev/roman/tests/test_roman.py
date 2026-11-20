import pytest
from src.roman import from_roman, to_roman


@pytest.mark.parametrize("text,n", [("I", 1), ("IV", 4), ("IX", 9), ("XL", 40), ("XC", 90),
                                    ("CD", 400), ("CM", 900), ("MCMXCIV", 1994), ("MMMCMXCIX", 3999),
                                    ("LVIII", 58)])
def test_from_roman(text, n):
    assert from_roman(text) == n


@pytest.mark.parametrize("bad", ["", "IIII", "IC", "VX", "ABC", "ix", "MMMM", "IIV", "XM"])
def test_rejects(bad):
    with pytest.raises(ValueError):
        from_roman(bad)


def test_round_trip():
    for n in range(1, 4000):
        assert from_roman(to_roman(n)) == n


def test_to_roman_range():
    with pytest.raises(ValueError):
        to_roman(0)
