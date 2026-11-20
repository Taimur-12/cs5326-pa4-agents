import pytest

from src.units import (UnitError, convert, convert_rate, format_quantity, humanize_duration,
                       pace_per_km, parse_quantity, total_length, wind_chill)


def approx(x):
    return pytest.approx(x, rel=1e-9, abs=1e-9)


def test_linear():
    assert convert(1, "mi", "km") == approx(1.609344)
    assert convert(2, "lb", "kg") == approx(0.90718474)
    assert convert(90, "min", "h") == approx(1.5)


def test_temperature():
    assert convert(300, "K", "F") == approx(80.33)
    assert convert(-40, "C", "F") == approx(-40)
    assert convert(212, "F", "C") == approx(100)
    assert convert(0, "C", "K") == approx(273.15)
    assert convert(50, "degF", "K") == approx(283.15)


def test_rates():
    assert convert_rate(36, "km/h", "m/s") == approx(10)
    assert convert_rate(1, "m/s", "km/h") == approx(3.6)
    assert convert_rate(60, "mi/h", "km/h") == approx(96.56064)
    assert convert_rate(2, "l/min", "ml/s") == approx(100 / 3)


def test_parse():
    assert parse_quantity("5 ft") == (5.0, "ft")
    assert parse_quantity("-40 °C") == (-40.0, "C")
    assert parse_quantity("1.5e3 m") == (1500.0, "m")
    assert parse_quantity("250 µm") == (250.0, "µm")
    assert parse_quantity("10km/h") == (10.0, "km/h")
    assert parse_quantity(".5 kg") == (0.5, "kg")
    assert parse_quantity("3. hours") == (3.0, "h")


@pytest.mark.parametrize("bad", ["abc", "5", "5 parsecs", "", "1..2 m", "km 5"])
def test_parse_errors(bad):
    with pytest.raises(UnitError):
        parse_quantity(bad)


def test_format():
    assert format_quantity(1234.5, "m") == "1230 m"
    assert format_quantity(0.0012345, "kg") == "0.00123 kg"
    assert format_quantity(0, "s") == "0 s"
    assert format_quantity(-98.76, "C", sig=2) == "-99 C"
    assert format_quantity(2.5, "h") == "2.5 h"
    assert format_quantity(99.96, "km") == "100 km"


def test_errors():
    with pytest.raises(UnitError):
        convert(1, "m", "kg")
    with pytest.raises(UnitError):
        convert(1, "C", "m")
    with pytest.raises(UnitError):
        convert_rate(1, "km/h", "kg/s")


def test_helpers_unchanged():
    assert humanize_duration(3725) == "1h 2m 5s"
    assert humanize_duration(0) == "0s"
    assert total_length(["1 km", "250 m"]) == approx(1250)
    assert pace_per_km(10, "km", 3000) == "5:00 /km"
    assert wind_chill(20, "C", 30, "km/h") == 20
    assert wind_chill(-10, "C", 20, "km/h") == pytest.approx(-17.87, abs=0.01)
