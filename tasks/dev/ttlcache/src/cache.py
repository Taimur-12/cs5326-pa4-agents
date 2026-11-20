"""A size-bounded cache with per-entry expiry. See ISSUE.md."""
import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity, ttl, clock=time.monotonic):
        self.capacity, self.ttl, self.clock = capacity, ttl, clock
        self._data = OrderedDict()   # key -> (value, set_time); oldest first

    def get(self, key, default=None):
        if key not in self._data:
            return default
        value, _ = self._data[key]
        self._data[key] = (value, self.clock())
        return value

    def set(self, key, value):
        if key not in self._data and len(self._data) >= self.capacity:
            self._data.popitem(last=True)
        self._data[key] = (value, self.clock())

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return list(self._data)
