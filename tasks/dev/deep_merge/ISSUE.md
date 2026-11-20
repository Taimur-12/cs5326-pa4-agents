# Bug: loading a user config wipes out nested defaults

`deep_merge(defaults, user)` is supposed to merge nested dicts recursively, with `user` winning on conflicts. Instead:

```python
defaults = {"db": {"host": "localhost", "port": 5432}, "debug": False}
deep_merge(defaults, {"db": {"port": 6000}})
# got:      {"db": {"port": 6000}, "debug": False}
# expected: {"db": {"host": "localhost", "port": 6000}, "debug": False}
```

Worse, after the call `defaults` itself has changed. Neither input may ever be modified, and the result must not share any nested dict with the inputs (changing the result later must never change `defaults`). A non-dict value in `user` simply replaces whatever was there.
