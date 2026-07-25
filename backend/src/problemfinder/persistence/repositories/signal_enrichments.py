"""Versioned enrichment rows: latest-version reads, append-only writes.

Recompute never overwrites: it appends a higher (signal_id, version) row and
readers take each signal's latest. History therefore shows what every past
ruleset concluded, which is the audit trail the method column promises.
"""

from collections.abc import Iterable, Sequence
from itertools import batched
from uuid import UUID

from sqlalchemy import Select, insert, select
from sqlalchemy.orm import Session

from problemfinder.domain.enrichment import SignalEnrichment
from problemfinder.persistence.mapping import enrichment_to_values, row_to_enrichment
from problemfinder.persistence.orm import SignalEnrichmentRow

_CHUNK = 500


def latest_rows() -> Select[tuple[SignalEnrichmentRow]]:
    """Selectable of each signal's highest-version enrichment row."""
    return (
        select(SignalEnrichmentRow)
        .distinct(SignalEnrichmentRow.signal_id)
        .order_by(SignalEnrichmentRow.signal_id, SignalEnrichmentRow.version.desc())
    )


def latest_for(session: Session, signal_ids: Iterable[UUID]) -> dict[UUID, SignalEnrichment]:
    """The latest enrichment per signal, for the signals that have one."""
    stmt = latest_rows().where(SignalEnrichmentRow.signal_id.in_(list(signal_ids)))
    return {row.signal_id: row_to_enrichment(row) for row in session.execute(stmt).scalars()}


def append_many(session: Session, enrichments: Sequence[SignalEnrichment]) -> int:
    """Insert new (signal_id, version) rows; existing versions are never touched."""
    written = 0
    for chunk in batched(enrichments, _CHUNK, strict=False):
        values = [enrichment_to_values(enrichment) for enrichment in chunk]
        session.execute(insert(SignalEnrichmentRow).values(values))
        written += len(values)  # a plain insert lands every row or raises
    return written
