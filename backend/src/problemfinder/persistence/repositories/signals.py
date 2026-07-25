"""Idempotent signal writes.

Identity is deterministic (UUIDv5 of source and external id), so reingesting
the same evidence conflicts on the primary key and is skipped; the returned
counts feed the run ledger. A batch is also deduped against itself first:
one payload repeating an external id must never crash a write or inflate the
stored count, whichever path it arrives through.
"""

from collections.abc import Iterator, Sequence
from itertools import batched
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from problemfinder.persistence.mapping import AnySignal, row_to_signal, signal_to_values
from problemfinder.persistence.orm import SignalRow

_CHUNK = 500


def _first_per_id(signals: Sequence[AnySignal]) -> list[AnySignal]:
    """The first occurrence of each id, in input order."""
    seen: set[UUID] = set()
    unique: list[AnySignal] = []
    for signal in signals:
        if signal.id not in seen:
            seen.add(signal.id)
            unique.append(signal)
    return unique


def stream_all(session: Session, chunk_size: int = _CHUNK) -> Iterator[list[AnySignal]]:
    """Every stored signal as a domain model, in id-ordered chunks.

    Keyset pagination rather than one long-lived cursor, so callers can write
    through the same session between chunks and rows committed mid-iteration
    (a live crawl, say) are picked up rather than skipped.
    """
    last: UUID | None = None
    while True:
        stmt = select(SignalRow).order_by(SignalRow.id).limit(chunk_size)
        if last is not None:
            stmt = stmt.where(SignalRow.id > last)
        rows = session.execute(stmt).scalars().all()
        if not rows:
            return
        last = rows[-1].id
        yield [row_to_signal(row) for row in rows]


def upsert_many(session: Session, signals: Sequence[AnySignal]) -> tuple[int, int]:
    """Insert signals, skipping ids already stored. Returns (stored, skipped)."""
    stored = 0
    for chunk in batched(_first_per_id(signals), _CHUNK, strict=False):
        stmt = (
            insert(SignalRow)
            .values([signal_to_values(signal) for signal in chunk])
            .on_conflict_do_nothing(index_elements=["id"])
            .returning(SignalRow.id)
        )
        stored += len(session.execute(stmt).fetchall())
    return stored, len(signals) - stored


def overwrite_many(session: Session, signals: Sequence[AnySignal]) -> int:
    """Insert or replace signals in place, keeping their stable ids.

    Reparse semantics: every regenerated signal overwrites its row wholesale,
    provenance included, because this run is now the row's producer. Returns
    the number of rows written.
    """
    written = 0
    for chunk in batched(_first_per_id(signals), _CHUNK, strict=False):
        values = [signal_to_values(signal) for signal in chunk]
        stmt = insert(SignalRow).values(values)
        replacements = {name: stmt.excluded[name] for name in values[0] if name != "id"}
        replace = stmt.on_conflict_do_update(index_elements=["id"], set_=replacements).returning(
            SignalRow.id
        )
        written += len(session.execute(replace).fetchall())
    return written
