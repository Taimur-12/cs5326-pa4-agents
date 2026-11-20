import pytest

from src.cursor import decode_cursor, encode_cursor
from src.pages import paginate

ORDERS = [{"id": i, "status": "paid" if i % 3 else "refunded"} for i in (5, 1, 9, 3, 7, 2, 8, 6, 4)]


def walk(page_size, **kw):
    pages, cursor = [], None
    while True:
        r = paginate(ORDERS, page_size, cursor, **kw)
        pages.append([it["id"] for it in r["items"]])
        cursor = r["next_cursor"]
        if cursor is None:
            return pages
        assert len(pages) < 20, "pagination never ends"


def test_walks_every_item_once_in_order():
    assert walk(4) == [[1, 2, 3, 4], [5, 6, 7, 8], [9]]


def test_exact_final_page_has_no_cursor():
    assert walk(3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert walk(9) == [[1, 2, 3, 4, 5, 6, 7, 8, 9]]


def test_status_filter_fills_pages():
    assert walk(2, status="paid") == [[1, 2], [4, 5], [7, 8]]
    assert walk(5, status="refunded") == [[3, 6, 9]]
    assert paginate(ORDERS, 3, status="cancelled") == {"items": [], "next_cursor": None}


def test_other_key_and_string_keys():
    people = [{"name": n} for n in ["mo", "al", "zed", "bea"]]
    first = paginate(people, 2, key="name")
    assert [p["name"] for p in first["items"]] == ["al", "bea"]
    second = paginate(people, 2, first["next_cursor"], key="name")
    assert [p["name"] for p in second["items"]] == ["mo", "zed"] and second["next_cursor"] is None


def test_cursor_round_trip_and_missing_key():
    for k in [0, 42, "abc", "with spaces/and+symbols"]:
        assert decode_cursor(encode_cursor(k)) == k
    # the cursor's item may have been deleted since: continue after its key anyway
    r = paginate([it for it in ORDERS if it["id"] != 4], 2, encode_cursor(4))
    assert [it["id"] for it in r["items"]] == [5, 6]


@pytest.mark.parametrize("bad", ["", "not-base64!!", "e30=", "bnVsbA==", "eyJhZnRlciI6"])
def test_bad_cursors(bad):
    with pytest.raises(ValueError):
        paginate(ORDERS, 3, bad)


@pytest.mark.parametrize("size", [0, 101, 2.5, "3"])
def test_bad_page_size(size):
    with pytest.raises(ValueError):
        paginate(ORDERS, size)
