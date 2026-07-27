"""Workbook bytes -> one record per (firm, product group) with complaints.

The modern era (2016 H2 onwards) carries the same logical table in every
release: a row per firm, a column per product group, one sheet per metric.
Sheet names drift ('Opened' vs '(1.3) Opened' vs '(1.3) Open') and older
sheets put the header under two preamble rows, so sheets are matched by
normalised name and the header row is located by its 'Firm Name' cell.
"""

from collections.abc import Callable, Iterator

import fastexcel
from pydantic import JsonValue

from problemfinder.sources.adapters.fca_complaints_returns.periods import row_period_bounds
from problemfinder.sources.cells import count, share, text
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError
from problemfinder.sources.slugs import slug

_SHEET_NAMES = {
    "opened": ("opened", "open"),
    "upheld": ("percentage upheld", "upheld"),
    "closed": ("closed",),
}
_PRODUCT_START_COL = 4
_HINT_KEYS = ("period", "period_start", "period_end", "page_url")


def parse_workbook(raw: RawDocument) -> Iterator[ParsedRecord]:
    hints = raw.work_item.request_hints
    period = str(hints.get("period", raw.work_item.external_id))
    opened, upheld, closed = _load_tables(raw.content)
    products, rows = _table(opened)
    upheld_by_firm = _metric_lookup(upheld, share)
    closed_by_firm = _metric_lookup(closed, count)
    for row in rows:
        firm = text(row[0])
        if firm is None:
            continue
        for offset, product in enumerate(products):
            volume = count(row[_PRODUCT_START_COL + offset])
            if volume is None or volume <= 0:
                continue
            key = (firm.casefold(), product)
            fields: dict[str, JsonValue] = {
                "firm_name": firm,
                "firm_group": text(row[1]),
                "joint_reporting": text(row[2]),
                "reporting_period": text(row[3]),
                "category": product,
                "volume": volume,
                "upheld_share": upheld_by_firm.get(key),
                "closed": closed_by_firm.get(key),
                **row_period_bounds(text(row[3])),
                **{k: hints.get(k) for k in _HINT_KEYS},
            }
            yield ParsedRecord(external_id=f"{period}:{slug(firm)}:{slug(product)}", fields=fields)


Rows = list[tuple[object, ...]]


def _load_tables(content: bytes) -> tuple[Rows, Rows, Rows]:
    try:
        workbook = fastexcel.read_excel(content)

        def rows_of(kind: str) -> Rows:
            name = _sheet_named(workbook.sheet_names, kind)
            return workbook.load_sheet_by_name(name, header_row=None).to_polars().rows()

        return rows_of("opened"), rows_of("upheld"), rows_of("closed")
    except (fastexcel.FastExcelError, KeyError) as exc:
        raise SourceParseError(f"not a firm-level complaints workbook: {exc}") from exc


def _sheet_named(names: list[str], kind: str) -> str:
    """Match by name normalised of its '(N.N)' prefix and whitespace drift."""
    wanted = _SHEET_NAMES[kind]
    for name in names:
        bare = name.split(")", 1)[-1].strip().casefold()
        if bare in wanted:
            return name
    raise KeyError(f"no {kind} sheet in {names}")


def _table(rows: Rows) -> tuple[list[str], Rows]:
    """(product-group labels, firm rows) from a metric sheet's raw rows.

    The header cell reads 'Firm Name' in every sheet except the 2016 upheld
    sheet, which kept its pivot-table export label 'Row Labels'.
    """
    for index, row in enumerate(rows):
        first = (text(row[0]) or "").casefold()
        if first.startswith(("firm name", "row labels")):
            products = [label for cell in row[_PRODUCT_START_COL:] if (label := text(cell))]
            return products, rows[index + 1 :]
    raise SourceParseError("metric sheet has no 'Firm Name' header row")


def _metric_lookup(
    rows: Rows, coerce: Callable[[object], float | int | None]
) -> dict[tuple[str, str], float | int]:
    products, data = _table(rows)
    lookup: dict[tuple[str, str], float | int] = {}
    for row in data:
        firm = text(row[0])
        if firm is None:
            continue
        for offset, product in enumerate(products):
            value = coerce(row[_PRODUCT_START_COL + offset])
            if value is not None:
                lookup[(firm.casefold(), product)] = value
    return lookup
