"""Workbook bytes -> one record per (firm, product group) with complaints.

The modern era (2016 H2 onwards) carries the same logical table in every
release: a row per firm, a column per product group, one sheet per metric.
Presentation drifts by year — sheet names ('Opened', '(1.3) Open',
'% upheld '), preamble rows above the header, and the 2017-2019 files
prepend a hidden row-id column and a duplicated Firm Name column — so
sheets are matched by normalised name and every column is located by its
header label, never by position.
"""

from collections.abc import Callable, Iterator
from typing import NamedTuple

import fastexcel
from pydantic import JsonValue

from problemfinder.sources.adapters.fca_complaints_returns.periods import row_period_bounds
from problemfinder.sources.cells import count, share, text
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError
from problemfinder.sources.slugs import slug

_SHEET_NAMES = {
    "opened": ("opened", "open"),
    "upheld": ("percentage upheld", "upheld", "% upheld"),
    "closed": ("closed",),
}
_HINT_KEYS = ("period", "period_start", "period_end", "page_url")


def parse_workbook(raw: RawDocument) -> Iterator[ParsedRecord]:
    hints = raw.work_item.request_hints
    period = str(hints.get("period", raw.work_item.external_id))
    opened, upheld, closed = _load_tables(raw.content)
    layout, rows = _table(opened)
    upheld_by_firm = _metric_lookup(upheld, share)
    closed_by_firm = _metric_lookup(closed, count)
    for row in rows:
        firm = text(row[layout.firm])
        if firm is None:
            continue
        for column, product in layout.products:
            volume = count(row[column])
            if volume is None or volume <= 0:
                continue
            key = (firm.casefold(), product)
            reporting_period = text(row[layout.period])
            fields: dict[str, JsonValue] = {
                "firm_name": firm,
                "firm_group": text(row[layout.group]) if layout.group is not None else None,
                "joint_reporting": text(row[layout.joint]) if layout.joint is not None else None,
                "reporting_period": reporting_period,
                "category": product,
                "volume": volume,
                "upheld_share": upheld_by_firm.get(key),
                "closed": closed_by_firm.get(key),
                **row_period_bounds(reporting_period),
                **{k: hints.get(k) for k in _HINT_KEYS},
            }
            yield ParsedRecord(external_id=f"{period}:{slug(firm)}:{slug(product)}", fields=fields)


Rows = list[tuple[object, ...]]


class _Layout(NamedTuple):
    """Column indices found from header labels; products as (index, label)."""

    firm: int
    group: int | None
    joint: int | None
    period: int
    products: list[tuple[int, str]]


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


def _table(rows: Rows) -> tuple[_Layout, Rows]:
    """(column layout, firm rows) from a metric sheet's raw rows.

    The firm column reads 'Firm Name' everywhere except the 2016 upheld
    sheet's pivot-export label 'Row Labels'. Product-group columns are
    whatever carries a label after the reporting-period column, which
    also steps over the 2017-2019 duplicated Firm Name column.
    """
    for index, row in enumerate(rows):
        labels = [(text(cell) or "").casefold() for cell in row]
        firm = _labelled(labels, ("firm name", "row labels"))
        period = _labelled(labels, ("reporting period",))
        if firm is None or period is None:
            continue
        products = [
            (column, label)
            for column in range(period + 1, len(row))
            if (label := text(row[column]))
        ]
        layout = _Layout(
            firm=firm,
            group=_labelled(labels, ("firm group", "group")),
            joint=_labelled(labels, ("joint",)),
            period=period,
            products=products,
        )
        return layout, rows[index + 1 :]
    raise SourceParseError("metric sheet has no 'Firm Name' header row")


def _labelled(labels: list[str], prefixes: tuple[str, ...]) -> int | None:
    return next(
        (i for i, label in enumerate(labels) if label.startswith(prefixes)),
        None,
    )


def _metric_lookup(
    rows: Rows, coerce: Callable[[object], float | int | None]
) -> dict[tuple[str, str], float | int]:
    layout, data = _table(rows)
    lookup: dict[tuple[str, str], float | int] = {}
    for row in data:
        firm = text(row[layout.firm])
        if firm is None:
            continue
        for column, product in layout.products:
            value = coerce(row[column])
            if value is not None:
                lookup[(firm.casefold(), product)] = value
    return lookup
