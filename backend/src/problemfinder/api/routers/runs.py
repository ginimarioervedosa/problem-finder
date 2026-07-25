"""The run ledger: every pipeline execution, newest first."""

from typing import Annotated

from fastapi import APIRouter, Query

from problemfinder.api.dependencies import SessionDep
from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.queries.run_ledger import recent_runs

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("")
def list_runs(
    session: SessionDep,
    source_key: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[IngestionRun]:
    return recent_runs(session, source_key=source_key, limit=limit)
