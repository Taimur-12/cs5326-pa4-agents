# Rate limiter blocks the wrong clients

`SlidingWindowLimiter` in `src/ratelimit.py` protects our public API. Since it shipped:

- One noisy client gets *every* client throttled.
- A client that keeps retrying while throttled stays throttled long after it should have recovered.
- `retry_after` always says "wait the full window", even when a slot frees up sooner.
- Invalid settings (limit 0, window 0) are accepted.

Intended behaviour of `SlidingWindowLimiter(limit, window_s, clock=time.monotonic)`:

- Each key is limited independently.
- `allow(key)` returns `True` and records the request if fewer than `limit` **allowed** requests for that key happened in the last `window_s` seconds; otherwise returns `False` and records nothing. A request that happened exactly `window_s` seconds ago no longer counts.
- `pending(key)`: number of allowed requests for the key that still count.
- `retry_after(key)`: `0` if a request would be allowed now, otherwise the seconds until the oldest counted request stops counting.
- `reset(key)` forgets a key. `active_keys()` returns the sorted keys that have at least one counted request; keys with none must not be kept around (the service sees millions of distinct keys).
- `ValueError` if `limit < 1` or `window_s <= 0`.
