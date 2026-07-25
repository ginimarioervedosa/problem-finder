"""The ingestion pipeline. Stage order is a tested invariant:

    compliance gate -> discover -> fetch -> ARCHIVE -> parse -> normalise
    -> dedupe-on-store -> cursor advance

Archive-before-parse is the hard requirement that makes parsers disposable:
history can always be reparsed without refetching. One failing item never
aborts a run; it lands in the run's error ledger instead.
"""

from datetime import UTC, datetime
from uuid import uuid4

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.domain.provenance import Provenance
from problemfinder.ingestion import archive, compliance
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import ingestion_runs, raw_payloads, signals
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


async def run_source(source_key: str, limit: int | None = None) -> IngestionRun:
    """Ingest one source end to end and return the finished run record."""
    source = registry.get(source_key)
    compliance.check(source.policy)

    run = IngestionRun(id=uuid4(), source_key=source.key, started_at=datetime.now(tz=UTC))
    with session_scope() as session:
        ingestion_runs.record(session, run)

    counts = {"fetched": 0, "parsed": 0, "stored_new": 0, "deduplicated": 0}
    errors: list[str] = []
    done: list[WorkItem] = []
    async for item in source.discover(None):
        if limit is not None and len(done) >= limit:
            break
        try:
            await _process_item(source, item, run, counts)
            done.append(item)
        except Exception as exc:  # one bad item must not abort the run
            errors.append(f"{item.external_id}: {exc}")

    finished = run.model_copy(
        update={
            "finished_at": datetime.now(tz=UTC),
            "cursor_after": source.cursor_after(None, done) if done else None,
            "errors": errors,
            **counts,
        }
    )
    with session_scope() as session:
        ingestion_runs.record(session, finished)
    return finished


async def _process_item(
    source: Source, item: WorkItem, run: IngestionRun, counts: dict[str, int]
) -> None:
    raw = await source.fetch(item)
    counts["fetched"] += 1
    meta = archive.store(raw, source.key, source.version)
    provenance = Provenance(
        raw_payload_sha256=meta.sha256,
        adapter_version=source.version,
        ingestion_run_id=run.id,
        fetched_at=raw.fetched_at,
    )
    normalised = [source.normalise(record, provenance) for record in source.parse(raw)]
    counts["parsed"] += len(normalised)
    with session_scope() as session:
        raw_payloads.add_if_absent(session, meta)
        stored, skipped = signals.upsert_many(session, normalised)
    counts["stored_new"] += stored
    counts["deduplicated"] += skipped
