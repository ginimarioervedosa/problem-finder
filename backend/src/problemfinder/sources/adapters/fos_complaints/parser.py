"""Workbook bytes -> one record per (business, category) with complaints.

The 'New cases' sheet has a two-row header (categories on row two) and totals
plus footnote rows at the tail; 'Resolved cases' carries per-category upheld
shares. Category columns are derived from the header, not hardcoded, because
the category set changes across years.
"""

import re
from collections.abc import Iterator

import fastexcel
import polars as pl
from pydantic import JsonValue

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_DATA_START_ROW = 2
_CATEGORY_START_COL = 3


def parse_workbook(raw: RawDocument) -> Iterator[ParsedRecord]:
    hints = raw.work_item.request_hints
    period = str(hints.get("period", raw.work_item.external_id))
    new_cases, resolved = _load_sheets(raw.content)
    categories = _categories(new_cases)
    upheld = _upheld_lookup(resolved)
    for row in new_cases.rows()[_DATA_START_ROW:]:
        business = _text(row[0])
        if business is None or _is_totals_or_footnote(business):
            continue
        volumes = [_int(cell) or 0 for cell in row[3 : 3 + len(categories)]]
        for category, volume in zip(categories, volumes, strict=False):
            if volume <= 0:
                continue
            fields: dict[str, JsonValue] = {
                "business_name": business,
                "business_group": _text(row[1]),
                "category": category,
                "volume": volume,
                "upheld_share": _category_share(upheld.get(business, {}), category),
                "total_new_cases": _int(row[2]),
                **{
                    k: hints.get(k)
                    for k in ("period_start", "period_end", "page_url", "published_at")
                },
                "period": period,
            }
            yield ParsedRecord(
                external_id=f"{period}:{_slug(business)}:{_slug(category)}", fields=fields
            )


def _load_sheets(content: bytes) -> tuple[pl.DataFrame, pl.DataFrame]:
    try:
        workbook = fastexcel.read_excel(content)
        by_name = {name.casefold(): name for name in workbook.sheet_names}
        new_cases = by_name["new cases"]
        resolved = by_name["resolved cases"]
        load = workbook.load_sheet_by_name
        return (
            load(new_cases, header_row=None).to_polars(),
            load(resolved, header_row=None).to_polars(),
        )
    except (fastexcel.FastExcelError, KeyError) as exc:
        raise SourceParseError(f"not a FOS business complaints workbook: {exc}") from exc


def _categories(new_cases: pl.DataFrame) -> list[str]:
    if new_cases.height < _DATA_START_ROW:
        raise SourceParseError("New cases sheet has no header rows")
    header = new_cases.rows()[1]
    return [text for cell in header[_CATEGORY_START_COL:] if (text := _text(cell))]


def _upheld_lookup(resolved: pl.DataFrame) -> dict[str, dict[str, float]]:
    rows = resolved.rows()
    if not rows:
        return {}
    headers = [_text(cell) or "" for cell in rows[0]]
    lookup: dict[str, dict[str, float]] = {}
    for row in rows[1:]:
        business = _text(row[0])
        if business is None or _is_totals_or_footnote(business):
            continue
        shares = {
            header: share
            for header, cell in zip(headers, row, strict=False)
            if "% of cases upheld" in header and (share := _share(cell)) is not None
        }
        lookup[business] = shares
    return lookup


def _category_share(shares: dict[str, float], category: str) -> float | None:
    for header, share in shares.items():
        if header.startswith(category):
            return share
    return None


def _is_totals_or_footnote(business: str) -> bool:
    lowered = business.lower()
    return lowered.startswith("*") or "total number of complaints" in lowered


def _text(cell: object) -> str | None:
    text = str(cell).strip() if cell is not None else ""
    return text or None


def _int(cell: object) -> int | None:
    if isinstance(cell, bool) or cell is None:
        return None
    if isinstance(cell, int | float):
        return int(cell)
    cleaned = str(cell).strip().replace(",", "")
    return int(float(cleaned)) if re.fullmatch(r"-?\d+(\.\d+)?", cleaned) else None


def _share(cell: object) -> float | None:
    if isinstance(cell, bool) or cell is None:
        return None
    if isinstance(cell, int | float):
        value = float(cell)
    else:
        cleaned = str(cell).strip().rstrip("%")
        if not re.fullmatch(r"-?\d+(\.\d+)?", cleaned):
            return None
        value = float(cleaned)
    return value / 100 if value > 1 else value


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
