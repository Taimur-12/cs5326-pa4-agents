"""Plain-text tables for CLI reports."""


def display_width(s):
    """Number of terminal columns the string occupies."""
    return len(s)


def format_table(rows, headers, align=None, max_width=None):
    """Format rows under headers as a text table."""
    align = align or "l" * len(headers)
    cells = [[str(c) for c in headers]] + [[str(c) for c in r] for r in rows]
    if max_width:
        cells = [[c if len(c) <= max_width else c[:max_width - 1] + "…" for c in row] for row in cells]
    widths = [max(display_width(row[i]) for row in cells) for i in range(len(headers))]
    lines = []
    for row in cells:
        parts = []
        for i, c in enumerate(row):
            if align[i] == "r":
                parts.append(c.rjust(widths[i]))
            elif align[i] == "c":
                parts.append(c.center(widths[i]))
            else:
                parts.append(c.ljust(widths[i]))
        lines.append(" | ".join(parts))
    sep = "-+-".join("-" * w for w in widths)
    return "\n".join([lines[0], sep] + lines[1:])
