"""Filtered, paginated signal search backing the drill-down grid."""

from datetime import date

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session

from problemfinder.domain.signal import SignalKind
from problemfinder.persistence.mapping import AnySignal, row_to_signal
from problemfinder.persistence.orm import SignalRow


class SignalFilters(BaseModel):
    """Every dashboard filter; None means 'no constraint'."""

    source_key: str | None = None
    kind: SignalKind | None = None
    firm: str | None = None
    category: str | None = None
    period_from: date | None = None
    period_to: date | None = None
    search: str | None = None


def effective_date() -> ColumnElement[date]:
    """Aggregates sit on their period end; verbatims on their publication date."""
    return func.coalesce(SignalRow.period_end, func.date(SignalRow.published_at))


def apply_filters(
    stmt: Select[tuple[SignalRow]], filters: SignalFilters
) -> Select[tuple[SignalRow]]:
    if filters.source_key:
        stmt = stmt.where(SignalRow.source_key == filters.source_key)
    if filters.kind:
        stmt = stmt.where(SignalRow.kind == filters.kind.value)
    if filters.firm:
        stmt = stmt.where(SignalRow.firm_name.ilike(f"%{filters.firm}%"))
    if filters.category:
        stmt = stmt.where(SignalRow.category == filters.category)
    if filters.period_from:
        stmt = stmt.where(effective_date() >= filters.period_from)
    if filters.period_to:
        stmt = stmt.where(effective_date() <= filters.period_to)
    if filters.search:
        needle = f"%{filters.search}%"
        stmt = stmt.where(SignalRow.body.ilike(needle) | SignalRow.title.ilike(needle))
    return stmt


def search_signals(
    session: Session, filters: SignalFilters, limit: int = 50, offset: int = 0
) -> tuple[list[AnySignal], int]:
    """One page of matching signals plus the unpaginated total."""
    filtered = apply_filters(select(SignalRow), filters)
    total = session.execute(
        select(func.count()).select_from(filtered.order_by(None).subquery())
    ).scalar_one()
    page = filtered.order_by(
        effective_date().desc().nulls_last(), SignalRow.volume.desc().nulls_last(), SignalRow.id
    )
    rows = session.execute(page.limit(limit).offset(offset)).scalars()
    return [row_to_signal(row) for row in rows], total


def get_signal(session: Session, signal_id: str) -> AnySignal | None:
    row = session.get(SignalRow, signal_id)
    return row_to_signal(row) if row else None
