def median(xs):
    """Return the median of a non-empty list of numbers."""
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return s[mid]
    return s[mid]
