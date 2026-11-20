import pytest

from src.resolver import CycleError, MissingDependency, ResolveError, install_order


def test_simple():
    pk = {"app": ["web", "db"], "web": ["util"], "db": [], "util": []}
    assert install_order(pk, ["app"]) == ["db", "util", "web", "app"]


def test_alphabetical_tie_break():
    pk = {"a": ["z"], "b": [], "z": []}
    assert install_order(pk, ["a", "b"]) == ["b", "z", "a"]
    assert install_order(pk, ["b", "a"]) == ["b", "z", "a"]


def test_only_needed_and_once():
    pk = {"app": ["lib", "log"], "lib": ["log", "log"], "log": [], "unused": ["log"]}
    assert install_order(pk, ["app", "lib"]) == ["log", "lib", "app"]


def test_missing():
    with pytest.raises(MissingDependency) as e:
        install_order({"app": ["web"], "web": ["ghost"]}, ["app"])
    assert (e.value.name, e.value.required_by) == ("ghost", "web")
    assert isinstance(e.value, ResolveError)
    with pytest.raises(MissingDependency) as e:
        install_order({"app": []}, ["nope"])
    assert (e.value.name, e.value.required_by) == ("nope", None)


def test_optional():
    pk = {"web": ["cache?", "http"], "http": []}
    assert install_order(pk, ["web"]) == ["http", "web"]
    pk["cache"] = []
    assert install_order(pk, ["web"]) == ["cache", "http", "web"]


def test_cycle():
    pk = {"app": ["d"], "b": ["c"], "c": ["d"], "d": ["b"]}
    with pytest.raises(CycleError) as e:
        install_order(pk, ["app"])
    assert e.value.cycle == ["b", "c", "d", "b"]
    assert isinstance(e.value, ResolveError)


def test_self_cycle():
    with pytest.raises(CycleError) as e:
        install_order({"a": ["a"]}, ["a"])
    assert e.value.cycle == ["a", "a"]


def test_deep_chain():
    n = 5000
    pk = {f"p{i:05d}": [f"p{i + 1:05d}"] for i in range(n - 1)}
    pk[f"p{n - 1:05d}"] = []
    assert install_order(pk, ["p00000"]) == [f"p{i:05d}" for i in reversed(range(n))]
