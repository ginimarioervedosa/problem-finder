"""Monthly signal volumes per dimension key, for the trend lines.

A signal lands in the month of its effective date: period end for
aggregates, publication date for verbatims. Series are bounded to the top
keys by total volume so the chart stays readable.
"""

from datetime import date

from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from problemfinder.persistence.orm import SignalRow
from problemfinder.queries.signal_search import SignalFilters, apply_filters, effective_date
from problemfinder.queries.summaries import SummaryDimension, dimension_column


class TrendPoint(BaseModel):
    bucket: date
    key: str
    volume: int
    signals: int


def volume_over_time(
    session: Session, dimension: SummaryDimension, filters: SignalFilters, series: int = 8
) -> list[TrendPoint]:
    key = dimension_column(dimension)
    volume = func.sum(func.coalesce(SignalRow.volume, 1)).label("volume")
    top_keys = (
        apply_filters(select(SignalRow), filters)
        .with_only_columns(key)
        .where(key.is_not(None))
        .group_by(key)
        .order_by(func.sum(func.coalesce(SignalRow.volume, 1)).desc())
        .limit(series)
    )
    bucket = cast(func.date_trunc("month", effective_date()), Date).label("bucket")
    stmt = (
        apply_filters(select(SignalRow), filters)
        .with_only_columns(bucket, key.label("key"), volume, func.count().label("signals"))
        .where(key.in_(top_keys), effective_date().is_not(None))
        .group_by(bucket, key)
        .order_by(bucket, key)
    )
    return [
        TrendPoint(bucket=row.bucket, key=row.key, volume=row.volume, signals=row.signals)
        for row in session.execute(stmt)
    ]
