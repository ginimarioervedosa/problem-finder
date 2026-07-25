"""Idempotent signal writes.

Identity is deterministic (UUIDv5 of source and external id), so reingesting
the same evidence conflicts on the primary key and is skipped; the returned
counts feed the run ledger.
"""

from collections.abc import Sequence
from itertools import batched

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from problemfinder.persistence.mapping import AnySignal, signal_to_values
from problemfinder.persistence.orm import SignalRow

_CHUNK = 500


def upsert_many(session: Session, signals: Sequence[AnySignal]) -> tuple[int, int]:
    """Insert signals, skipping ids already stored. Returns (stored, skipped)."""
    stored = 0
    for chunk in batched(signals, _CHUNK, strict=False):
        stmt = (
            insert(SignalRow)
            .values([signal_to_values(signal) for signal in chunk])
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(SignalRow.id)
        )
        stored += len(session.execute(stmt).fetchall())
    return stored, len(signals) - stored
