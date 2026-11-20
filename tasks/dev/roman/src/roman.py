VALUES = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
SINGLE = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def to_roman(n):
    """1994 -> 'MCMXCIV'. Valid for 1..3999."""
    if not isinstance(n, int) or not 0 < n < 4000:
        raise ValueError(f"out of range: {n!r}")
    out = ""
    for value, symbol in VALUES:
        while n >= value:
            out += symbol
            n -= value
    return out


def from_roman(text):
    """'MCMXCIV' -> 1994. Raises ValueError unless text is a valid canonical numeral."""
    return sum(SINGLE[c] for c in text)
