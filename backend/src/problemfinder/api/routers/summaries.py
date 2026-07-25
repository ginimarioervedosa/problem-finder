"""Grouped volumes for the charts."""

from typing import Annotated

from fastapi import APIRouter, Query

from problemfinder.api.dependencies import FiltersDep, SessionDep
from problemfinder.queries.summaries import SummaryDimension, SummaryRow, volume_by

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/{dimension}")
def summarise(
    dimension: SummaryDimension,
    session: SessionDep,
    filters: FiltersDep,
    top: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[SummaryRow]:
    return volume_by(session, dimension, filters, top=top)
