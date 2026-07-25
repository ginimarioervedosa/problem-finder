"""Insert domain signals plus the provenance rows their foreign keys need."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from problemfinder.persistence.mapping import AnySignal, signal_to_values
from problemfinder.persistence.orm import IngestionRunRow, RawPayloadRow, SignalRow


def seed_signals(session: Session, signals: Sequence[AnySignal]) -> None:
    seed_provenance(session, signals)
    for signal in signals:
        session.add(SignalRow(**signal_to_values(signal)))
    session.flush()


def seed_provenance(session: Session, signals: Sequence[AnySignal]) -> None:
    """Insert only the payload and run rows the signals' foreign keys need."""
    for signal in signals:
        provenance = signal.provenance
        session.merge(
            RawPayloadRow(
                sha256=provenance.raw_payload_sha256,
                source_key=signal.source_key,
                url="https://example.org/payload",
                media_type="text/plain",
                size_bytes=1,
                http_status=200,
                fetched_at=provenance.fetched_at,
                relative_path=f"seed/{provenance.raw_payload_sha256}",
                adapter_version=provenance.adapter_version,
            )
        )
        session.merge(
            IngestionRunRow(
                id=provenance.ingestion_run_id,
                source_key=signal.source_key,
                started_at=provenance.fetched_at,
                finished_at=None,
                cursor_before=None,
                cursor_after=None,
                fetched=0,
                parsed=0,
                stored_new=0,
                deduplicated=0,
                errors=[],
            )
        )
    session.flush()
