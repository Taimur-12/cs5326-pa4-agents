"""Work out the order in which packages must be installed. See docs/RESOLVER.md."""


class ResolveError(Exception):
    pass


class CycleError(ResolveError):
    def __init__(self, cycle):
        super().__init__(" -> ".join(cycle))
        self.cycle = cycle


class MissingDependency(ResolveError):
    def __init__(self, name, required_by):
        super().__init__(f"{name} (required by {required_by})")
        self.name = name
        self.required_by = required_by


def install_order(packages, targets):
    """Return the packages needed by targets, dependencies first."""
    order, seen = [], set()

    def visit(name):
        if name in seen:
            return
        seen.add(name)
        for dep in packages[name]:
            visit(dep)
        order.append(name)

    for t in targets:
        visit(t)
    return order
