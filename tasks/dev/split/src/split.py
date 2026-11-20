"""Split an amount by weights. See ISSUE.md."""
from decimal import Decimal


def split(amount, weights):
    """Return one share per weight, summing to amount."""
    total = float(amount)
    wsum = sum(float(w) for w in weights)
    return [Decimal(str(round(total * float(w) / wsum, 2))).quantize(Decimal("0.01")) for w in weights]


def format_money(d):
    """'$1,234.50' style."""
    return f"${d:,.2f}"
