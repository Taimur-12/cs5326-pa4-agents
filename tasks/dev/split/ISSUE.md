# Bill splitting loses and invents cents

`split()` in `src/split.py` divides a bill between people by weight (e.g. by nights stayed), and `format_money()`
prints the amounts. Finance found:

- Shares do not always add up to the bill: `split("100.00", [1, 1, 1])` gives three times 33.33 (a cent vanishes).
- All-zero weights crash with `ZeroDivisionError`; negative weights are accepted.
- A refund (negative amount) is split wrongly.
- `format_money(Decimal("-1234.5"))` prints `$-1,234.50` instead of `-$1,234.50`.

The rules (finance's spec):

- `split(amount, weights)` takes the amount as a string or `Decimal` with at most 2 decimal places (else
  `ValueError`), and a non-empty list of non-negative numbers with at least one positive (else `ValueError`).
- It returns a list of `Decimal` amounts with exactly 2 decimal places, one per weight, that **sum exactly** to the
  amount, using the **largest remainder method**: give each person their exact share rounded *down* to the cent,
  then hand out the leftover cents one at a time to the people whose exact share had the largest remainder; ties go
  to the person listed **first**. A zero weight always gets `0.00`.
- A negative amount is split as its absolute value, then every share is negated.
- No floating point anywhere: weights may be ints, `Decimal`s or numeric strings.
- `format_money(d)`: `$` + thousands separators + exactly 2 decimals, with the minus sign before the `$`:
  `$1,234.50`, `-$0.05`, `$0.00`.
