"""Upheld-share lookup from the resolved sheet, across both workbook eras.

Modern files (2021 onwards) label each column "Category: Average % of cases
upheld" in a single header row. Legacy files (2009 to 2020) use a three-row
header: category names sit on the second row and shares are positional. Both
produce the same lookup: business -> {category label -> share}.
"""

import re

from problemfinder.sources.cells import share, text

_HEADER_SUFFIX = "% of cases upheld"
type Rows = list[tuple[object, ...]]


def upheld_lookup(rows: Rows) -> dict[str, dict[str, float]]:
    if not rows:
        return {}
    headers = [text(cell) or "" for cell in rows[0]]
    if any(":" in header and _HEADER_SUFFIX in header for header in headers):
        return _modern(headers, rows[1:])
    return _legacy(rows)


def category_share(shares: dict[str, float], category: str) -> float | None:
    """Match a new-cases category against either era's lookup keys."""
    for key, value in shares.items():
        if key.startswith(category):
            return value
    return None


def _modern(headers: list[str], data_rows: Rows) -> dict[str, dict[str, float]]:
    lookup: dict[str, dict[str, float]] = {}
    for row in data_rows:
        business = _business(row)
        if business is None:
            continue
        lookup[business] = {
            header: value
            for header, cell in zip(headers, row, strict=False)
            if _HEADER_SUFFIX in header and (value := share(cell)) is not None
        }
    return lookup


def _legacy(rows: Rows) -> dict[str, dict[str, float]]:
    if len(rows) < 2:
        return {}
    categories = {
        index: label for index, cell in enumerate(rows[1]) if index >= 3 and (label := text(cell))
    }
    lookup: dict[str, dict[str, float]] = {}
    for row in rows[2:]:
        business = _business(row)
        if business is None:
            continue
        lookup[business] = {
            label: value
            for index, label in categories.items()
            if index < len(row) and (value := share(row[index])) is not None
        }
    return lookup


def _business(row: tuple[object, ...]) -> str | None:
    business = text(row[0]) if row else None
    if business is None or business == "Business Name" or _is_noise(business):
        return None
    return business


def _is_noise(business: str) -> bool:
    lowered = business.lower()
    return lowered.startswith("*") or bool(re.search(r"total number of complaints", lowered))
