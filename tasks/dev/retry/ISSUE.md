# Retries make outages worse

Our HTTP clients wrap calls in `retry()` from `src/retry.py`, with the delay schedule in `src/backoff.py`. During
last week's outage it misbehaved:

- It sleeps once more after the final failed attempt, then raises a generic `RuntimeError`, so callers lose the
  real error.
- Delays grow without bound (we saw a 640-second sleep), and the `deadline` option is ignored.
- `Ctrl+C` during a retry loop is swallowed when `retry_on=(BaseException,)` is used.
- The `on_retry` callback numbers attempts from 0, unlike our logs (from 1).

Required behaviour, from the module docstrings:

- `attempts` is the total number of calls, including the first; it must be at least 1 (else `ValueError`).
- The delay before retry `k` (k = 1 for the first retry) is `min(max_delay, base_delay * factor ** (k - 1))`.
- `on_retry(n, exc, delay)` is called before each sleep, where `n` is the 1-based number of the attempt that
  just failed.
- After the last attempt fails, do not sleep: re-raise that exception itself.
- Exceptions not matching `retry_on` propagate at once, without sleeping. `KeyboardInterrupt` and `SystemExit`
  are never retried, whatever `retry_on` says.
- `deadline` (seconds, or `None`): if sleeping the next delay would make the total time slept exceed the deadline,
  stop retrying and re-raise the last exception.
