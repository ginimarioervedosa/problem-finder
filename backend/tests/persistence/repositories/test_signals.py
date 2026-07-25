"""A batch that repeats an id must dedupe against itself, not crash or miscount."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from problemfinder.domain.signal import VerbatimSignal
from problemfinder.persistence.orm import SignalRow
from problemfinder.persistence.repositories import signals
from tests.support.builders import build_provenance, build_verbatim
from tests.support.seeding import seed_provenance

pytestmark = pytest.mark.db


def _count(session: Session) -> int:
    return session.execute(select(func.count()).select_from(SignalRow)).scalar_one()


def duplicate_pair() -> tuple[VerbatimSignal, VerbatimSignal]:
    provenance = build_provenance()
    first = build_verbatim(body="original wording", provenance=provenance)
    repeat = build_verbatim(body="same id, different wording", provenance=provenance)
    return first, repeat


def test_upsert_skips_intra_batch_duplicates(db_session: Session) -> None:
    first, repeat = duplicate_pair()
    seed_provenance(db_session, [first])
    stored, skipped = signals.upsert_many(db_session, [first, repeat])
    assert (stored, skipped) == (1, 1)
    assert _count(db_session) == 1
    assert db_session.execute(select(SignalRow.body)).scalar_one() == "original wording"


def test_overwrite_survives_intra_batch_duplicates(db_session: Session) -> None:
    first, repeat = duplicate_pair()
    seed_provenance(db_session, [first])
    written = signals.overwrite_many(db_session, [first, repeat])
    assert written == 1
    assert _count(db_session) == 1
