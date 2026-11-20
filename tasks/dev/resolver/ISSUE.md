# `install_order` is unreliable

`src/resolver.py` decides the order our package manager installs packages in. Problems reported:

- The order sometimes differs from what the spec says, so lock files churn between runs.
- A dependency cycle is silently accepted instead of being reported.
- An unknown dependency crashes with a bare `KeyError`.
- Optional dependencies (`"cache?"`) are not understood at all.
- It crashes on one of our larger internal repositories.

The required behaviour is in `docs/RESOLVER.md`. Please make `install_order` follow it. The exception classes in the module are part of the public API.
