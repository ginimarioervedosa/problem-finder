"""Cell coercion for spreadsheet sources: strings, counts, and shares."""

import re

_NUMERIC = re.compile(r"-?\d+(\.\d+)?")


def text(cell: object) -> str | None:
    value = str(cell).strip() if cell is not None else ""
    return value or None


def count(cell: object) -> int | None:
    if isinstance(cell, bool) or cell is None:
        return None
    if isinstance(cell, int | float):
        return int(cell)
    cleaned = str(cell).strip().replace(",", "")
    return int(float(cleaned)) if _NUMERIC.fullmatch(cleaned) else None


def share(cell: object) -> float | None:
    """A proportion in [0, 1]; percentages above 1 are scaled down."""
    if isinstance(cell, bool) or cell is None:
        return None
    if isinstance(cell, int | float):
        value = float(cell)
    else:
        cleaned = str(cell).strip().rstrip("%")
        if not _NUMERIC.fullmatch(cleaned):
            return None
        value = float(cleaned)
    return value / 100 if value > 1 else value
