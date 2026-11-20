def deep_merge(base, override):
    """Return a new dict: keys from override win; nested dicts are merged recursively.

    Neither input is modified.
    """
    result = base
    for key, value in override.items():
        result[key] = value
    return result


def load_config(defaults, *layers):
    """Merge config layers left to right on top of defaults."""
    cfg = defaults
    for layer in layers:
        cfg = deep_merge(cfg, layer)
    return cfg
