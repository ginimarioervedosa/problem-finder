"""Workbook bytes -> one record per (business, category) with complaints.

The new-cases sheet is structurally stable across every era: a two-row header
(categories on row two, from column four) then one row per business, with
totals and footnote rows at the tail. Sheet names and the resolved sheet's
layout vary by era; sheet matching is by prefix and the upheld lookup handles
both formats.
"""

import re
from collections.abc import Iterator

import fastexcel
import polars as pl
from pydantic import JsonValue

from problemfinder.sources.adapters.fos_complaints.cells import count, text
from problemfinder.sources.adapters.fos_complaints.upheld import category_share, upheld_lookup
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_DATA_START_ROW = 2
_CATEGORY_START_COL = 3


def parse_workbook(raw: RawDocument) -> Iterator[ParsedRecord]:
    hints = raw.work_item.request_hints
    period = str(hints.get("period", raw.work_item.external_id))
    new_cases, resolved = _load_sheets(raw.content)
    categories = _categories(new_cases)
    upheld = upheld_lookup(resolved.rows())
    for row in new_cases.rows()[_DATA_START_ROW:]:
        business = text(row[0])
        if business is None or _is_totals_or_footnote(business):
            continue
        volumes = [count(cell) or 0 for cell in row[3 : 3 + len(categories)]]
        for category, volume in zip(categories, volumes, strict=False):
            if volume <= 0:
                continue
            fields: dict[str, JsonValue] = {
                "business_name": business,
                "business_group": text(row[1]),
                "category": category,
                "volume": volume,
                "upheld_share": category_share(upheld.get(business, {}), category),
                "total_new_cases": count(row[2]),
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
        new_cases = _sheet_named(workbook.sheet_names, "new")
        resolved = _sheet_named(workbook.sheet_names, "resolved")
        load = workbook.load_sheet_by_name
        return (
            load(new_cases, header_row=None).to_polars(),
            load(resolved, header_row=None).to_polars(),
        )
    except (fastexcel.FastExcelError, KeyError) as exc:
        raise SourceParseError(f"not a FOS business complaints workbook: {exc}") from exc


def _sheet_named(names: list[str], prefix: str) -> str:
    """Sheet names drift across eras ('New cases', 'New complaints'); match by prefix."""
    for name in names:
        if name.casefold().startswith(prefix):
            return name
    raise KeyError(f"no sheet starting with {prefix!r} in {names}")


def _categories(new_cases: pl.DataFrame) -> list[str]:
    if new_cases.height < _DATA_START_ROW:
        raise SourceParseError("new-cases sheet has no header rows")
    header = new_cases.rows()[1]
    return [label for cell in header[_CATEGORY_START_COL:] if (label := text(cell))]


def _is_totals_or_footnote(business: str) -> bool:
    lowered = business.lower()
    return lowered.startswith("*") or "total number of complaints" in lowered


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
