# Session cache evicts live sessions and serves expired ones

`TTLCache` in `src/cache.py` holds user sessions: at most `capacity` entries, each expiring `ttl` seconds after it
was **set**. Since the last deploy:

- Busy users get logged out: the cache evicts the entry that was used most recently, not least recently.
- Expired sessions still count toward capacity, so live sessions get evicted while dead ones sit in the cache.
- Reading a session extends its lifetime. It must not: only `set` starts a new lifetime.
- `len(cache)` counts expired entries.

Contract (`TTLCache(capacity, ttl, clock=time.monotonic)`):

- `capacity` must be an int >= 1 and `ttl` a positive number or `None` (never expires); else `ValueError`.
- An entry set at time `t` is live while `clock() < t + ttl`, and expired from `t + ttl` on.
- `get(key, default=None)`: the value if the entry is live (and it becomes the most recently used), else
  `default`. An expired entry is removed when found.
- `set(key, value)`: store the value, restart its lifetime and make it the most recently used. If this adds a key
  and the cache already holds `capacity` **live** entries, first evict the least recently used live entry. Expired
  entries never cause an eviction: drop them instead.
- `len(cache)` is the number of live entries; `key in cache` is true only for live keys (and does not change
  recency). `keys()` returns the live keys from least to most recently used.
