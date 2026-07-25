"""The run ledger, newest first, for the observability view."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.persistence.mapping import row_to_run
from problemfinder.persistence.orm import IngestionRunRow


def recent_runs(
    session: Session, source_key: str | None = None, limit: int = 50
) -> list[IngestionRun]:
    stmt = select(IngestionRunRow).order_by(IngestionRunRow.started_at.desc()).limit(limit)
    if source_key:
        stmt = stmt.where(IngestionRunRow.source_key == source_key)
    return [row_to_run(row) for row in session.execute(stmt).scalars()]
