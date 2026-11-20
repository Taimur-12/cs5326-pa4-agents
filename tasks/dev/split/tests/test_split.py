from decimal import Decimal as D

import pytest

from src.split import format_money, split


def test_sums_exactly():
    shares = split("100.00", [1, 1, 1])
    assert shares == [D("33.34"), D("33.33"), D("33.33")]
    assert sum(shares) == D("100.00")


def test_largest_remainder_not_first_come():
    # exact shares: 1.428.., 2.857.., 5.714.. -> floors 1.42, 2.85, 5.71 (sum 9.98); remainders .0085, .0071, .0042
    assert split("10.00", [1, 2, 4]) == [D("1.43"), D("2.86"), D("5.71")]


def test_ties_go_to_the_first_listed():
    assert split("0.05", [1, 1, 1, 1]) == [D("0.02"), D("0.01"), D("0.01"), D("0.01")]


def test_zero_weights_and_types():
    assert split("9.99", [0, 1, D("2"), "0"]) == [D("0.00"), D("3.33"), D("6.66"), D("0.00")]
    out = split(D("7"), ["1.5", "1.5"])
    assert out == [D("3.50"), D("3.50")] and all(x.as_tuple().exponent == -2 for x in out)


def test_negative_amount():
    assert split("-100.00", [1, 1, 1]) == [D("-33.34"), D("-33.33"), D("-33.33")]


@pytest.mark.parametrize("amount,weights", [("1.005", [1]), ("10", []), ("10", [0, 0]), ("10", [1, -1]),
                                            ("ten", [1])])
def test_errors(amount, weights):
    with pytest.raises(ValueError):
        split(amount, weights)


def test_format_money():
    assert format_money(D("1234.5")) == "$1,234.50"
    assert format_money(D("-1234.5")) == "-$1,234.50"
    assert format_money(D("-0.05")) == "-$0.05"
    assert format_money(D("0")) == "$0.00"
    assert format_money(D("1000000")) == "$1,000,000.00"
