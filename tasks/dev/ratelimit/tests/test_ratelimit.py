import pytest

from src.ratelimit import SlidingWindowLimiter


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make(limit=3, window=10.0):
    c = Clock()
    return c, SlidingWindowLimiter(limit, window, clock=c)


def test_limit_and_window_boundary():
    c, lim = make()
    assert [lim.allow("a") for _ in range(4)] == [True, True, True, False]
    c.t += 9.999
    assert not lim.allow("a")
    c.t = 1010.0
    assert lim.allow("a")


def test_denied_requests_do_not_count():
    c, lim = make(limit=2, window=10)
    lim.allow("a")
    c.t += 5
    lim.allow("a")
    c.t += 3
    assert not lim.allow("a")
    c.t = 1010.0
    assert lim.allow("a")
    assert lim.pending("a") == 2


def test_keys_independent():
    c, lim = make(limit=1)
    assert lim.allow("a")
    assert lim.allow("b")
    assert not lim.allow("a")
    assert lim.pending("b") == 1


def test_retry_after():
    c, lim = make(limit=2, window=10)
    assert lim.retry_after("a") == 0
    lim.allow("a")
    c.t += 4
    lim.allow("a")
    c.t += 1
    assert lim.retry_after("a") == pytest.approx(5.0)
    c.t += 5
    assert lim.retry_after("a") == 0
    assert lim.allow("a")


def test_reset_and_active_keys():
    c, lim = make()
    lim.allow("a")
    lim.allow("b")
    c.t += 6
    lim.allow("c")
    assert lim.active_keys() == ["a", "b", "c"]
    lim.reset("b")
    assert lim.active_keys() == ["a", "c"]
    c.t += 4
    assert lim.active_keys() == ["c"]
    c.t += 6
    assert lim.active_keys() == []
    assert lim.pending("zzz") == 0
    assert lim.active_keys() == []


def test_invalid():
    with pytest.raises(ValueError):
        SlidingWindowLimiter(0, 10)
    with pytest.raises(ValueError):
        SlidingWindowLimiter(1, 0)
