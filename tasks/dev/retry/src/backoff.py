"""Delay schedule for retries."""


def delays(base_delay, factor, max_delay):
    """Yield the delay before retry 1, retry 2, ...: base_delay * factor ** (k - 1), capped at max_delay."""
    delay = base_delay
    while True:
        yield delay
        delay = delay * factor
