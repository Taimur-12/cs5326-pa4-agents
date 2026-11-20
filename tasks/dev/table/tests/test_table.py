import pytest

from src.table import display_width, format_table


def test_basic():
    out = format_table([["apple", 3], ["kiwi", 12]], ["fruit", "n"])
    assert out == "fruit | n\n------+---\napple | 3\nkiwi  | 12"


def test_alignment():
    out = format_table([["a", 1], ["bbb", 100]], ["k", "v"], align="cr")
    assert out == " k  |   v\n----+----\n a  |   1\nbbb | 100"
    assert format_table([["abcde"]], ["ab"], align="c") == " ab\n-----\nabcde"


def test_display_width():
    assert display_width("abc") == 3
    assert display_width("漢字") == 4
    assert display_width("ｈｉ") == 4
    assert display_width("é") == 1


def test_wide_and_combining():
    out = format_table([["漢字", 1], ["abc", 22]], ["name", "n"])
    assert out == "name | n\n-----+---\n漢字 | 1\nabc  | 22"
    out = format_table([["café", "x"], ["tea", "y"]], ["drink", "k"])
    assert out == "drink | k\n------+--\ncafé  | x\ntea   | y"


def test_truncation():
    out = format_table([["漢字漢字", "abcdefgh"]], ["a", "b"], max_width=4)
    assert out == "a   | b\n----+-----\n漢… | abc…"
    assert format_table([["abcd"]], ["h"], max_width=4) == "h\n----\nabcd"


def test_none_and_numbers():
    assert format_table([[None, 1.5]], ["x", "y"]) == "x | y\n--+----\n  | 1.5"


@pytest.mark.parametrize("kwargs", [
    {"rows": [["a"]], "headers": ["x", "y"]},
    {"rows": [["a", "b"]], "headers": ["x", "y"], "align": "l"},
    {"rows": [["a", "b"]], "headers": ["x", "y"], "align": "lx"},
    {"rows": [["a", "b"]], "headers": ["x", "y"], "max_width": 1},
])
def test_errors(kwargs):
    with pytest.raises(ValueError):
        format_table(**kwargs)
