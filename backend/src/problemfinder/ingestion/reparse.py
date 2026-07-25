"""Replay the immutable archive through parse and normalise, no refetch.

Bump an adapter's version, run `pf reparse <source>`, and every signal is
regenerated from the archived payloads: identities stay stable (UUIDv5 of
source and external id), regenerated rows overwrite in place. Nothing is
collected, so the compliance gate is not re-run: archived history must stay
replayable even if a terms review has lapsed since. Reparse never deletes; a
parser change that stops yielding a record leaves the old signal standing.
"""

from datetime import UTC, datetime
from uuid import uuid4

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.raw_payload import RawPayloadMeta
from problemfinder.ingestion import archive
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import ingestion_runs, raw_payloads, signals
from problemfinder.sources import registry
from problemfinder.sources.protocol import RawDocument, Source, WorkItem


def reparse_source(source_key: str) -> IngestionRun:
    """Reparse every archived payload of one source; return the run record."""
    source = registry.get(source_key)
    run = IngestionRun(id=uuid4(), source_key=source.key, started_at=datetime.now(tz=UTC))
    with session_scope() as session:
        ingestion_runs.record(session, run)
        metas = raw_payloads.list_for_source(session, source.key)

    counts = {"parsed": 0, "stored_new": 0}
    errors: list[str] = []
    for meta in metas:
        try:
            produced, written = _reparse_payload(source, meta, run)
        except Exception as exc:  # one bad payload must not abort the replay
            errors.append(f"{meta.sha256[:12]}: {exc}")
            continue
        counts["parsed"] += produced
        counts["stored_new"] += written

    finished = run.model_copy(
        update={"finished_at": datetime.now(tz=UTC), "errors": errors, **counts}
    )
    with session_scope() as session:
        ingestion_runs.record(session, finished)
    return finished


def _reparse_payload(source: Source, meta: RawPayloadMeta, run: IngestionRun) -> tuple[int, int]:
    if meta.external_id is None:
        raise ValueError("payload predates work-item capture; cannot rebuild the parse input")
    raw = RawDocument(
        work_item=WorkItem(
            external_id=meta.external_id,
            url=meta.url,
            request_hints=meta.request_hints,
        ),
        content=archive.load(meta.relative_path),
        media_type=meta.media_type,
        fetched_at=meta.fetched_at,
        http_status=meta.http_status,
    )
    provenance = Provenance(
        raw_payload_sha256=meta.sha256,
        adapter_version=source.version,
        ingestion_run_id=run.id,
        fetched_at=meta.fetched_at,
    )
    regenerated = [source.normalise(record, provenance) for record in source.parse(raw)]
    with session_scope() as session:
        written = signals.overwrite_many(session, regenerated)
    return len(regenerated), written
