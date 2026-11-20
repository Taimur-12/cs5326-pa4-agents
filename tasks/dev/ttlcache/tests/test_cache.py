import pytest

from src.cache import TTLCache


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def make(capacity=3, ttl=10):
    c = Clock()
    return c, TTLCache(capacity, ttl, clock=c)


def test_lru_eviction_respects_reads():
    c, cache = make()
    for k in "abc":
        cache.set(k, k.upper())
    assert cache.get("a") == "A"          # a is now most recent
    cache.set("d", "D")                   # evicts b, the least recently used
    assert cache.keys() == ["c", "a", "d"] and "b" not in cache


def test_updating_existing_key_does_not_evict():
    c, cache = make()
    for k in "abc":
        cache.set(k, 1)
    cache.set("a", 2)
    assert cache.keys() == ["b", "c", "a"] and cache.get("a") == 2 and len(cache) == 3


def test_expiry_boundary_and_get_does_not_extend():
    c, cache = make(ttl=10)
    cache.set("s", "session")
    c.t = 105.0
    assert cache.get("s") == "session"
    c.t = 109.999
    assert cache.get("s") == "session"
    c.t = 110.0
    assert cache.get("s") is None and cache.get("s", "gone") == "gone"


def test_set_restarts_lifetime():
    c, cache = make(ttl=10)
    cache.set("s", 1)
    c.t = 108.0
    cache.set("s", 2)
    c.t = 115.0
    assert cache.get("s") == 2


def test_expired_entries_do_not_force_evictions():
    c, cache = make(capacity=2, ttl=10)
    cache.set("old", 1)
    c.t = 105.0
    cache.set("live", 2)
    c.t = 111.0                           # old expired, live still live
    assert len(cache) == 1 and "old" not in cache and "live" in cache
    cache.set("new", 3)                   # room: the expired entry must not cost a live one
    assert cache.keys() == ["live", "new"]


def test_contains_does_not_touch_recency():
    c, cache = make(capacity=2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert "a" in cache
    cache.set("c", 3)
    assert cache.keys() == ["b", "c"]


def test_no_ttl_never_expires():
    c, cache = make(ttl=None)
    cache.set("k", 1)
    c.t = 1e12
    assert cache.get("k") == 1 and len(cache) == 1


@pytest.mark.parametrize("cap,ttl", [(0, 10), (2.5, 10), (2, 0), (2, -1), ("2", 10)])
def test_validation(cap, ttl):
    with pytest.raises(ValueError):
        TTLCache(cap, ttl)
