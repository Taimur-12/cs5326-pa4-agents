import pytest

from src.backoff import delays
from src.retry import retry


class Flaky:
    def __init__(self, failures, exc=ConnectionError, result="ok"):
        self.failures, self.exc, self.result, self.calls = failures, exc, result, 0

    def __call__(self):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc(f"fail {self.calls}")
        return self.result


def run(fn, **kw):
    slept, seen = [], []
    out = retry(fn, sleep=slept.append, on_retry=lambda n, e, d: seen.append((n, str(e), d)), **kw)
    return out, slept, seen


def test_succeeds_after_failures():
    out, slept, seen = run(Flaky(2), attempts=3, base_delay=1, factor=2)
    assert out == "ok" and slept == [1, 2]
    assert seen == [(1, "fail 1", 1), (2, "fail 2", 2)]


def test_reraises_last_error_without_final_sleep():
    f = Flaky(5)
    slept = []
    with pytest.raises(ConnectionError, match="fail 3"):
        retry(f, attempts=3, base_delay=1, sleep=slept.append)
    assert f.calls == 3 and slept == [1, 2]


def test_delays_are_capped():
    gen = delays(1, 3, 10)
    assert [next(gen) for _ in range(5)] == [1, 3, 9, 10, 10]
    slept = []
    with pytest.raises(ConnectionError):
        retry(Flaky(9), attempts=6, base_delay=1, factor=3, max_delay=10, sleep=slept.append)
    assert slept == [1, 3, 9, 10, 10]


def test_non_matching_errors_propagate_immediately():
    f, slept = Flaky(1, exc=KeyError), []
    with pytest.raises(KeyError):
        retry(f, retry_on=(ConnectionError,), sleep=slept.append)
    assert f.calls == 1 and slept == []


def test_interrupts_are_never_retried():
    for exc in (KeyboardInterrupt, SystemExit):
        f, slept = Flaky(1, exc=exc), []
        with pytest.raises(exc):
            retry(f, retry_on=(BaseException,), sleep=slept.append)
        assert f.calls == 1 and slept == []


def test_deadline():
    f, slept = Flaky(10), []
    with pytest.raises(ConnectionError, match="fail 3"):
        retry(f, attempts=10, base_delay=1, factor=2, deadline=4, sleep=slept.append)
    assert slept == [1, 2] and f.calls == 3   # 1 + 2 + 4 would exceed 4
    out, slept, _ = run(Flaky(2), attempts=3, base_delay=1, factor=2, deadline=3)
    assert out == "ok" and slept == [1, 2]   # exactly the deadline is fine


def test_attempts_validation_and_single_attempt():
    with pytest.raises(ValueError):
        retry(lambda: 1, attempts=0)
    f, slept = Flaky(1), []
    with pytest.raises(ConnectionError):
        retry(f, attempts=1, sleep=slept.append)
    assert slept == [] and f.calls == 1
