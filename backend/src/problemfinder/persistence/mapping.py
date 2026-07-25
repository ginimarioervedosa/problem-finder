"""The one deliberate domain <-> ORM translation layer.

Pydantic domain models stay pure; these functions are the only place the two
representations meet. tests/persistence/test_mapping_parity.py asserts the
column set and the domain field set can never drift apart silently.
"""

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.enrichment import SignalEnrichment
from problemfinder.domain.identity import content_fingerprint
from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal, SignalKind, VerbatimSignal
from problemfinder.persistence.orm import CursorRow, IngestionRunRow, SignalEnrichmentRow, SignalRow

type AnySignal = VerbatimSignal | AggregateSignal


def signal_to_values(signal: AnySignal) -> dict[str, object]:
    """Column values for inserting one signal, whichever kind it is."""
    verbatim = signal if isinstance(signal, VerbatimSignal) else None
    aggregate = signal if isinstance(signal, AggregateSignal) else None
    return {
        "id": signal.id,
        "source_key": signal.source_key,
        "external_id": signal.external_id,
        "kind": signal.kind.value,
        "url": str(signal.url),
        "published_at": signal.published_at,
        "retrieved_at": signal.retrieved_at,
        "title": signal.title,
        "body": signal.body,
        "language": signal.language,
        "firm_name": signal.firm_name,
        "category": signal.category,
        "extras": signal.extras,
        "author_handle": verbatim.author_handle if verbatim else None,
        "period_start": aggregate.period_start if aggregate else None,
        "period_end": aggregate.period_end if aggregate else None,
        "volume": aggregate.volume if aggregate else None,
        "upheld_share": aggregate.upheld_share if aggregate else None,
        "denominator": aggregate.denominator if aggregate else None,
        "raw_payload_sha256": signal.provenance.raw_payload_sha256,
        "adapter_version": signal.provenance.adapter_version,
        "ingestion_run_id": signal.provenance.ingestion_run_id,
        "fetched_at": signal.provenance.fetched_at,
        "dedupe_hash": content_fingerprint(signal.source_key, signal.external_id, signal.body),
    }


def row_to_signal(row: SignalRow) -> AnySignal:
    """Rehydrate the right domain variant from a stored row."""
    payload: dict[str, object] = {
        "kind": row.kind,
        "id": row.id,
        "source_key": row.source_key,
        "external_id": row.external_id,
        "url": row.url,
        "published_at": row.published_at,
        "retrieved_at": row.retrieved_at,
        "title": row.title,
        "body": row.body,
        "language": row.language,
        "firm_name": row.firm_name,
        "category": row.category,
        "extras": row.extras,
        "provenance": Provenance(
            raw_payload_sha256=row.raw_payload_sha256,
            adapter_version=row.adapter_version,
            ingestion_run_id=row.ingestion_run_id,
            fetched_at=row.fetched_at,
        ),
    }
    if row.kind == SignalKind.AGGREGATE:
        payload |= {
            "period_start": row.period_start,
            "period_end": row.period_end,
            "volume": row.volume,
            "upheld_share": row.upheld_share,
            "denominator": row.denominator,
        }
        return AggregateSignal.model_validate(payload)
    payload["author_handle"] = row.author_handle
    return VerbatimSignal.model_validate(payload)


def enrichment_to_values(enrichment: SignalEnrichment) -> dict[str, object]:
    """Column values for one enrichment row; field names match columns one to one."""
    return enrichment.model_dump()


def row_to_enrichment(row: SignalEnrichmentRow) -> SignalEnrichment:
    return SignalEnrichment.model_validate(
        {name: getattr(row, name) for name in SignalEnrichment.model_fields}
    )


def run_to_values(run: IngestionRun) -> dict[str, object]:
    values = run.model_dump()
    values["cursor_before"] = (
        run.cursor_before.model_dump(mode="json") if run.cursor_before else None
    )
    values["cursor_after"] = run.cursor_after.model_dump(mode="json") if run.cursor_after else None
    return values


def cursor_to_values(cursor: Cursor) -> dict[str, object]:
    values: dict[str, object] = cursor.model_dump(mode="json")
    values["updated_at"] = cursor.updated_at  # DateTime column, not JSONB
    return values


def row_to_cursor(row: CursorRow) -> Cursor:
    return Cursor.model_validate(
        {"source_key": row.source_key, "state": row.state, "updated_at": row.updated_at}
    )


def row_to_run(row: IngestionRunRow) -> IngestionRun:
    payload: dict[str, object] = {
        "id": row.id,
        "source_key": row.source_key,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "cursor_before": Cursor.model_validate(row.cursor_before) if row.cursor_before else None,
        "cursor_after": Cursor.model_validate(row.cursor_after) if row.cursor_after else None,
        "fetched": row.fetched,
        "parsed": row.parsed,
        "stored_new": row.stored_new,
        "deduplicated": row.deduplicated,
        "errors": row.errors,
    }
    return IngestionRun.model_validate(payload)
