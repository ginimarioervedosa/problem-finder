"""The run ledger: every pipeline execution is recorded, start and finish."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.persistence.mapping import row_to_run, run_to_values
from problemfinder.persistence.orm import IngestionRunRow


def record(session: Session, run: IngestionRun) -> None:
    """Insert or update the run row; called at start and again at finish."""
    session.merge(IngestionRunRow(**run_to_values(run)))


def latest_for_source(session: Session, source_key: str) -> IngestionRun | None:
    stmt = (
        select(IngestionRunRow)
        .where(IngestionRunRow.source_key == source_key)
        .order_by(IngestionRunRow.started_at.desc())
        .limit(1)
    )
    row = session.execute(stmt).scalar_one_or_none()
    return row_to_run(row) if row else None
