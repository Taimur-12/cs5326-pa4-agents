from src.config import deep_merge, load_config

DEFAULTS = {"db": {"host": "localhost", "port": 5432, "opts": {"ssl": False, "pool": 5}}, "debug": False}


def fresh():
    import copy
    return copy.deepcopy(DEFAULTS)


def test_nested_merge():
    assert deep_merge(fresh(), {"db": {"port": 6000}}) == {
        "db": {"host": "localhost", "port": 6000, "opts": {"ssl": False, "pool": 5}}, "debug": False}


def test_three_levels():
    out = deep_merge(fresh(), {"db": {"opts": {"ssl": True}}})
    assert out["db"]["opts"] == {"ssl": True, "pool": 5}
    assert out["db"]["host"] == "localhost"


def test_non_dict_replaces():
    assert deep_merge(fresh(), {"db": None})["db"] is None
    assert deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}


def test_inputs_untouched():
    base, over = fresh(), {"db": {"port": 1}}
    deep_merge(base, over)
    assert base == DEFAULTS and over == {"db": {"port": 1}}


def test_no_shared_nested_dicts():
    base = fresh()
    out = deep_merge(base, {})
    out["db"]["opts"]["pool"] = 99
    assert base["db"]["opts"]["pool"] == 5


def test_load_config_layers():
    cfg = load_config(fresh(), {"debug": True}, {"db": {"host": "prod"}})
    assert cfg["debug"] is True and cfg["db"]["host"] == "prod" and cfg["db"]["port"] == 5432
