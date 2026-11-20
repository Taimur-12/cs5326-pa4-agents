"""Retry a call with exponential backoff. See ISSUE.md for the contract."""
import time

from .backoff import delays


def retry(fn, *, attempts=3, base_delay=0.5, factor=2.0, max_delay=10.0, retry_on=(Exception,),
          deadline=None, sleep=time.sleep, on_retry=None):
    """Call fn() until it succeeds or the attempts run out; return its result."""
    schedule = delays(base_delay, factor, max_delay)
    for i in range(attempts):
        try:
            return fn()
        except retry_on as e:
            delay = next(schedule)
            if on_retry is not None:
                on_retry(i, e, delay)
            sleep(delay)
    raise RuntimeError("retries exhausted")
