"""Sliding-window rate limiter."""
import time
from collections import deque


class SlidingWindowLimiter:
    def __init__(self, limit, window_s, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window_s, clock
        self._hits = deque()

    def _prune(self, now):
        while self._hits and self._hits[0] < now - self.window:
            self._hits.popleft()

    def allow(self, key):
        now = self.clock()
        self._prune(now)
        self._hits.append(now)
        return len(self._hits) <= self.limit

    def pending(self, key):
        self._prune(self.clock())
        return len(self._hits)

    def retry_after(self, key):
        return 0.0 if self.pending(key) < self.limit else float(self.window)

    def reset(self, key):
        self._hits.clear()

    def active_keys(self):
        return []
