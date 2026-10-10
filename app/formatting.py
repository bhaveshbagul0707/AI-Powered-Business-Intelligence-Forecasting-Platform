"""Indian currency and digit-grouping helpers shared by the dashboard."""
from __future__ import annotations


def indian_number(value: float, decimals: int = 0) -> str:
    """Format a number with Indian digit grouping, such as 12,34,567.50."""
    formatted = f"{abs(value):.{decimals}f}"
    whole, separator, fraction = formatted.partition(".")
    if len(whole) > 3:
        prefix, last_group = whole[:-3], whole[-3:]
        groups = []
        while prefix:
            groups.insert(0, prefix[-2:])
            prefix = prefix[:-2]
        whole = ",".join([*groups, last_group])
    sign = "-" if value < 0 else ""
    decimal_part = f".{fraction}" if separator else ""
    return f"{sign}{whole}{decimal_part}"


def indian_currency(value: float, decimals: int = 0) -> str:
    """Format a rupee amount using Indian digit grouping."""
    return f"{'-' if value < 0 else ''}₹{indian_number(abs(value), decimals)}"
