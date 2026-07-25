"""Grouped volumes for the charts: one query, one dimension at a time.

Volume counts an aggregate signal at its stated volume and a verbatim as one
voice; upheld shares are volume-weighted across rows that report an outcome.
"""

from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from problemfinder.persistence.orm import SignalRow
from problemfinder.queries.signal_search import SignalFilters, apply_filters


class SummaryDimension(StrEnum):
    CATEGORY = "category"
    FIRM = "firm"
    SOURCE = "source"


class SummaryRow(BaseModel):
    key: str
    volume: int
    signals: int
    upheld_share: float | None


_DIMENSION_COLUMNS: dict[
    SummaryDimension, InstrumentedAttribute[str] | InstrumentedAttribute[str | None]
] = {
    SummaryDimension.CATEGORY: SignalRow.category,
    SummaryDimension.FIRM: SignalRow.firm_name,
    SummaryDimension.SOURCE: SignalRow.source_key,
}


def volume_by(
    session: Session, dimension: SummaryDimension, filters: SignalFilters, top: int = 20
) -> list[SummaryRow]:
    key = _DIMENSION_COLUMNS[dimension]
    volume = func.sum(func.coalesce(SignalRow.volume, 1)).label("volume")
    weighted = func.sum(SignalRow.upheld_share * SignalRow.volume).filter(
        SignalRow.upheld_share.is_not(None)
    )
    weight = func.sum(SignalRow.volume).filter(SignalRow.upheld_share.is_not(None))
    stmt = (
        apply_filters(select(SignalRow), filters)
        .with_only_columns(
            key.label("key"),
            volume,
            func.count().label("signals"),
            (weighted / func.nullif(weight, 0)).label("upheld_share"),
        )
        .where(key.is_not(None))
        .group_by(key)
        .order_by(volume.desc())
        .limit(top)
    )
    return [
        SummaryRow(
            key=row.key, volume=row.volume, signals=row.signals, upheld_share=row.upheld_share
        )
        for row in session.execute(stmt)
    ]
