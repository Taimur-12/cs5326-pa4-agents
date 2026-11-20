# Text tables are misaligned for non-ASCII data

`format_table` in `src/table.py` prints the plain-text tables in our CLI reports. They come out misaligned as soon as the data contains Chinese/Japanese names or accented letters typed with combining marks, and a few other things are off. The required behaviour:

- **Display width:** `display_width(s)` is how many terminal columns `s` takes. Characters whose `unicodedata.east_asian_width` is `"W"` or `"F"` take 2 columns; combining characters (`unicodedata.combining(c) != 0`) take 0; everything else takes 1. All padding and alignment use display width, not `len`.
- **Cells:** `None` becomes an empty cell; anything else is converted with `str`.
- **Layout:** a header line, a separator line, then one line per row. Columns are joined with `" | "`. Each column is as wide as its widest cell (header included). The separator is one `-` per column of width for each column, joined with `"-+-"`. No line has trailing whitespace.
- **Alignment:** `align` is a string with one letter per column: `l` (left, default), `r` (right) or `c` (centre). When centring leaves an odd number of spaces, the extra space goes on the **right**. Headers use the same alignment as their column.
- **Truncation:** if `max_width` is given, any cell wider than `max_width` is cut to at most `max_width - 1` display columns, without splitting a wide character, and `…` (1 column) is appended.
- **Errors:** `ValueError` if a row has the wrong number of cells, `align` has the wrong length or a letter other than `l`/`r`/`c`, or `max_width < 2`.
