"""Monthly volume trends per dimension for the line chart."""

from typing import Annotated

from fastapi import APIRouter, Query

from problemfinder.api.dependencies import FiltersDep, SessionDep
from problemfinder.queries.summaries import SummaryDimension
from problemfinder.queries.trends import TrendPoint, volume_over_time

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("/{dimension}")
def trend(
    dimension: SummaryDimension,
    session: SessionDep,
    filters: FiltersDep,
    series: Annotated[int, Query(ge=1, le=20)] = 8,
) -> list[TrendPoint]:
    return volume_over_time(session, dimension, filters, series=series)
