"""Ranked problem themes for the dashboard."""

from typing import Annotated

from fastapi import APIRouter, Query

from problemfinder.api.dependencies import FiltersDep, SessionDep
from problemfinder.queries.themes import RankedTheme, ranked_themes

router = APIRouter(prefix="/api/themes", tags=["themes"])


@router.get("")
def ranked(
    session: SessionDep,
    filters: FiltersDep,
    top: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[RankedTheme]:
    return ranked_themes(session, filters, top=top)
