"""Unit conversion helpers shared by the weather and logistics dashboards.

Public API
----------
parse_quantity(text) -> (value, unit)
    Parse "12.5 km", "-40 °C", "1.5e3 m", ".5 kg", "250 µm", "10km/h". The number may have a sign,
    a decimal point (".5" and "3." are fine) and an exponent. Spaces between number and unit are
    optional. The unit is returned in canonical form (aliases resolved, e.g. "°C" -> "C"), and
    rate units like "km/h" are allowed. Raises UnitError for anything else.

convert(value, from_unit, to_unit) -> float
    Linear units convert through the base unit of their dimension. Temperatures (C, F, K) convert
    with the proper offsets. Raises UnitError for unknown units or different dimensions.

convert_rate(value, from_unit, to_unit) -> float
    Compound "a/b" units, e.g. 36 km/h -> 10 m/s. Numerator and denominator dimensions must match.

format_quantity(value, unit, sig=3) -> str
    Round to `sig` significant figures and write without an exponent, dropping trailing zeros
    after the decimal point and a trailing ".": 1234.5 -> "1230 m", 0.0012345 -> "0.00123 kg",
    2.5 -> "2.5 h", 0 -> "0 s".

Other helpers (humanize_duration, total_length, pace_per_km, wind_chill) are used by the
dashboards directly.
"""
import math
import re

# --------------------------------------------------------------------------------------------
# Unit tables: factor to the base unit of each dimension (m, kg, s, l).
# --------------------------------------------------------------------------------------------
LENGTH = {
    "µm": 1e-6, "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344, "nmi": 1852.0,
}
MASS = {
    "mg": 1e-6, "g": 0.001, "kg": 1.0, "t": 1000.0,
    "oz": 0.028349523125, "lb": 0.45359237,
}
TIME = {
    "ms": 0.001, "s": 1.0, "min": 60.0, "h": 3600.0, "d": 86400.0, "wk": 604800.0,
}
VOLUME = {
    "ml": 0.001, "l": 1.0, "m3": 1000.0, "gal": 3.785411784,
}
DIMENSIONS = {"length": LENGTH, "mass": MASS, "time": TIME, "volume": VOLUME}
TEMPERATURES = ("C", "F", "K")

ALIASES = {
    "um": "µm", "micron": "µm", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "kilometer": "km", "kilometre": "km", "mile": "mi", "miles": "mi", "foot": "ft", "feet": "ft",
    "gram": "g", "grams": "g", "kilo": "kg", "kilos": "kg", "lbs": "lb", "pound": "lb",
    "sec": "s", "secs": "s", "second": "s", "seconds": "s", "mins": "min", "minute": "min",
    "hr": "h", "hrs": "h", "hour": "h", "hours": "h", "day": "d", "days": "d",
    "litre": "l", "liter": "l", "L": "l", "mL": "ml",
    "°C": "C", "degC": "C", "celsius": "C", "°F": "F", "degF": "F", "fahrenheit": "F",
    "kelvin": "K",
}


class UnitError(ValueError):
    """Unknown unit, incompatible units, or unparseable quantity."""


# --------------------------------------------------------------------------------------------
# Unit lookup
# --------------------------------------------------------------------------------------------
def canonical(unit):
    """Resolve aliases; raise UnitError for unknown units."""
    unit = unit.strip()
    unit = ALIASES.get(unit, unit)
    if unit in TEMPERATURES or dimension_of(unit) is not None:
        return unit
    raise UnitError(f"unknown unit: {unit!r}")


def dimension_of(unit):
    """Name of the dimension a (canonical) linear unit belongs to, or None."""
    for name, table in DIMENSIONS.items():
        if unit in table:
            return name
    return None


def is_temperature(unit):
    return ALIASES.get(unit, unit) in TEMPERATURES


def factor(unit):
    """Factor from a linear unit to its base unit."""
    unit = canonical(unit)
    dim = dimension_of(unit)
    if dim is None:
        raise UnitError(f"{unit!r} is not a linear unit")
    return DIMENSIONS[dim][unit]


# --------------------------------------------------------------------------------------------
# Temperatures
# --------------------------------------------------------------------------------------------
def _to_kelvin(value, unit):
    if unit == "K":
        return value
    if unit == "C":
        return value + 273.15
    if unit == "F":
        return (value - 32) * 5 / 9 + 273.15
    raise UnitError(f"not a temperature: {unit!r}")


def _from_kelvin(value, unit):
    if unit == "K":
        return value
    if unit == "C":
        return value - 273.15
    if unit == "F":
        return (value - 273.15) * 9 / 5 - 32
    raise UnitError(f"not a temperature: {unit!r}")


# --------------------------------------------------------------------------------------------
# Conversion
# --------------------------------------------------------------------------------------------
def convert(value, from_unit, to_unit):
    """Convert value between two units of the same dimension."""
    a, b = canonical(from_unit), canonical(to_unit)
    if a in TEMPERATURES or b in TEMPERATURES:
        if not (a in TEMPERATURES and b in TEMPERATURES):
            raise UnitError(f"cannot convert {a} to {b}")
        return _from_kelvin(_to_kelvin(value, a), b)
    if dimension_of(a) != dimension_of(b):
        raise UnitError(f"cannot convert {a} ({dimension_of(a)}) to {b} ({dimension_of(b)})")
    return value * factor(a) / factor(b)


def _split_rate(unit):
    if unit.count("/") != 1:
        raise UnitError(f"not a rate unit: {unit!r}")
    num, den = unit.split("/")
    return canonical(num), canonical(den)


def convert_rate(value, from_unit, to_unit):
    """Convert a compound unit such as km/h."""
    fn, fd = _split_rate(from_unit)
    tn, td = _split_rate(to_unit)
    if is_temperature(fn) or is_temperature(tn):
        raise UnitError("temperatures cannot be used in rates")
    return value * convert(1, fn, tn) * convert(1, fd, td)


# --------------------------------------------------------------------------------------------
# Parsing and formatting
# --------------------------------------------------------------------------------------------
_QUANTITY = re.compile(r"^(\d+(?:\.\d+)?)\s*([A-Za-z/°]+)$")


def _canonical_any(unit):
    if "/" in unit:
        num, den = _split_rate(unit)
        return f"{num}/{den}"
    return canonical(unit)


def parse_quantity(text):
    """Parse '12.5 km' into (12.5, 'km'). See the module docstring."""
    m = _QUANTITY.match(text.strip())
    if not m:
        raise UnitError(f"cannot parse {text!r}")
    return float(m.group(1)), _canonical_any(m.group(2))


def _round_sig(x, sig):
    return round(x, sig - int(math.log10(abs(x))))


def format_quantity(value, unit, sig=3):
    """Format value with unit, rounded to sig significant figures."""
    return f"{_round_sig(value, sig)} {unit}"


# --------------------------------------------------------------------------------------------
# Dashboard helpers (used directly by the dashboards; behaviour must not change)
# --------------------------------------------------------------------------------------------
def humanize_duration(seconds):
    """3725 -> '1h 2m 5s'; 0 -> '0s'. Negative durations get a leading '-'."""
    sign = "-" if seconds < 0 else ""
    seconds = int(round(abs(seconds)))
    if seconds == 0:
        return "0s"
    parts = []
    for size, label in ((86400, "d"), (3600, "h"), (60, "m"), (1, "s")):
        n, seconds = divmod(seconds, size)
        if n:
            parts.append(f"{n}{label}")
    return sign + " ".join(parts)


def total_length(items, unit="m"):
    """Sum quantities like ['1 km', '250 m'] into the given unit."""
    total = 0.0
    for item in items:
        value, u = parse_quantity(item)
        total += convert(value, u, unit)
    return total


def pace_per_km(distance, distance_unit, seconds):
    """Running pace as 'M:SS /km'."""
    km = convert(distance, distance_unit, "km")
    if km <= 0:
        raise UnitError("distance must be positive")
    per_km = seconds / km
    minutes, secs = divmod(int(round(per_km)), 60)
    return f"{minutes}:{secs:02d} /km"


def wind_chill(temp, temp_unit, wind, wind_unit):
    """Wind chill in the same temperature unit (North American formula, valid <= 10 C)."""
    t = convert(temp, temp_unit, "C")
    v = convert_rate(wind, wind_unit, "km/h")
    if t > 10 or v < 4.8:
        return temp
    wc = 13.12 + 0.6215 * t - 11.37 * v ** 0.16 + 0.3965 * t * v ** 0.16
    return convert(wc, "C", temp_unit)


def clamp(value, lo, hi):
    """Clamp value into [lo, hi]."""
    return max(lo, min(hi, value))


def describe(value, unit):
    """Human label used in tooltips: '12.5 km (length)'."""
    u = canonical(unit)
    kind = "temperature" if u in TEMPERATURES else dimension_of(u)
    return f"{format_quantity(value, u)} ({kind})"
