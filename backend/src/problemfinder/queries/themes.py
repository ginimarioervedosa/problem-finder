"""Ranked problem themes: how often, how heavy, how corroborated, which way.

Themes are verbatim-led (aggregate bodies are formulaic, so they rarely carry
one); wherever an aggregate is tagged its stated volume still counts. Both
weightings ship in one row so the dashboard toggle needs no second query, and
the trend columns compare the two most recent half-year windows because the
corpus's aggregate cadence is half-yearly.
"""

from datetime import date, timedelta

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from problemfinder.persistence.orm import SignalRow
from problemfinder.persistence.repositories.signal_enrichments import latest_rows
from problemfinder.queries.signal_search import SignalFilters, apply_filters, effective_date

_HALF_YEAR = timedelta(days=183)


class RankedTheme(BaseModel):
    theme: str
    signals: int
    volume: int
    severity_weighted: float
    corroborating_sources: int
    recent_volume: int
    previous_volume: int


def ranked_themes(
    session: Session, filters: SignalFilters, top: int = 50, today: date | None = None
) -> list[RankedTheme]:
    anchor = today or date.today()
    recent_from = anchor - _HALF_YEAR
    previous_from = recent_from - _HALF_YEAR
    latest = latest_rows().subquery()
    weight = func.coalesce(SignalRow.volume, 1)
    stmt = (
        apply_filters(select(SignalRow), filters)
        .join(latest, latest.c.signal_id == SignalRow.id)
        .with_only_columns(
            latest.c.theme.label("theme"),
            func.count().label("signals"),
            func.sum(weight).label("volume"),
            func.sum(func.coalesce(latest.c.severity, 0.0) * weight).label("severity_weighted"),
            func.count(func.distinct(SignalRow.source_key)).label("corroborating_sources"),
            func.coalesce(func.sum(weight).filter(effective_date() >= recent_from), 0).label(
                "recent_volume"
            ),
            func.coalesce(
                func.sum(weight).filter(
                    effective_date() >= previous_from, effective_date() < recent_from
                ),
                0,
            ).label("previous_volume"),
        )
        .where(latest.c.theme.is_not(None))
        .group_by(latest.c.theme)
        .order_by(func.sum(weight).desc())
        .limit(top)
    )
    return [
        RankedTheme(
            theme=row.theme,
            signals=row.signals,
            volume=row.volume,
            severity_weighted=row.severity_weighted,
            corroborating_sources=row.corroborating_sources,
            recent_volume=row.recent_volume,
            previous_volume=row.previous_volume,
        )
        for row in session.execute(stmt)
    ]
