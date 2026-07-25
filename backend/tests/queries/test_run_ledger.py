"""The ledger lists runs newest first, optionally per source."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.persistence.repositories import ingestion_runs
from problemfinder.queries.run_ledger import recent_runs

pytestmark = pytest.mark.db


def make_run(source_key: str, day: int) -> IngestionRun:
    return IngestionRun(
        id=uuid4(),
        source_key=source_key,
        started_at=datetime(2026, 7, day, tzinfo=UTC),
        stored_new=day,
    )


@pytest.fixture
def seeded(db_session: Session) -> Session:
    for run in (make_run("fos_complaints", 1), make_run("reddit", 2), make_run("reddit", 3)):
        ingestion_runs.record(db_session, run)
    db_session.flush()
    return db_session


def test_runs_come_newest_first(seeded: Session) -> None:
    runs = recent_runs(seeded)
    assert [run.started_at.day for run in runs] == [3, 2, 1]


def test_source_filter_and_limit_apply(seeded: Session) -> None:
    runs = recent_runs(seeded, source_key="reddit", limit=1)
    assert [run.source_key for run in runs] == ["reddit"]
    assert runs[0].started_at.day == 3
