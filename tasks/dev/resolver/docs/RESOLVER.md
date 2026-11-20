# Install order

`install_order(packages, targets)`:

- `packages` maps a package name to the list of names it depends on.
- A dependency name ending in `?` is **optional**: if that package is not in `packages`, it is ignored; if it is, it is an ordinary dependency. A dependency may be listed more than once.
- The result lists every package the `targets` need, directly or transitively (including the targets themselves), **each exactly once**, and every package appears **after all of its dependencies**. Packages the targets do not need are not included.
- **Determinism:** whenever more than one package could be installed next, the alphabetically smallest one goes first. For example, with `a -> z` and `b` (no dependencies) and targets `["a", "b"]`, the order is `["b", "z", "a"]`. The order of `targets` does not matter.

## Errors

All errors are subclasses of `ResolveError`.

- An unknown target, or a non-optional dependency that is not in `packages`, raises `MissingDependency` with `.name` (the missing package) and `.required_by` (the package that needs it, or `None` for a target).
- A dependency cycle raises `CycleError` with `.cycle`: the package names along the cycle, following dependency edges, **starting and ending with the alphabetically smallest package in the cycle**. If `b -> c -> d -> b`, then `.cycle == ["b", "c", "d", "b"]`. A package that depends on itself gives `["a", "a"]`.

## Scale

Some internal repositories have dependency chains several thousand packages deep.
