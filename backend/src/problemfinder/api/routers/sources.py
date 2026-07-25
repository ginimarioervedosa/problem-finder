"""Source inventory: policy, enablement, and last run, for the provenance UI."""

from fastapi import APIRouter

from problemfinder.api.dependencies import SessionDep
from problemfinder.api.responses import SourceInfo
from problemfinder.persistence.repositories.ingestion_runs import latest_for_source
from problemfinder.sources.config import enabled_sources
from problemfinder.sources.registry import all_sources

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("")
def list_sources(session: SessionDep) -> list[SourceInfo]:
    enabled = enabled_sources()
    return [
        SourceInfo(
            key=source.key,
            version=source.version,
            enabled=source.key in enabled,
            policy=source.policy,
            last_run=latest_for_source(session, source.key),
        )
        for source in all_sources().values()
    ]
