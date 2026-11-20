# Dashboard shows wrong numbers after the units refactor

The weather and logistics dashboards both go through `src/units.py`. Since the refactor:

- The weather page shows 300 K as 16.33 °F; it should be about 80.33 °F.
- The fleet page shows a truck doing 36 km/h as 129600000 m/s; it should be 10 m/s.
- Pasting values like `-40 °C`, `1.5e3 m`, `.5 kg` or `250 µm` into the converter fails with "cannot parse".
- Formatted values look like `1230.0 m` instead of `1230 m`, and formatting zero crashes.

The intended API and behaviour are documented in the module docstring. Other helpers in the module are used elsewhere and must keep working.
