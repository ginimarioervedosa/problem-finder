"""Canned domain objects for tests; override any field per test."""

from datetime import UTC, date, datetime
from uuid import uuid4

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal, VerbatimSignal


def build_provenance() -> Provenance:
    return Provenance(
        raw_payload_sha256="a" * 64,
        adapter_version=1,
        ingestion_run_id=uuid4(),
        fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def build_aggregate(**overrides: object) -> AggregateSignal:
    payload: dict[str, object] = {
        "source_key": "fos_complaints",
        "external_id": "h1-2025:firm:banking",
        "url": "https://example.org/data",
        "published_at": None,
        "retrieved_at": datetime(2026, 7, 1, tzinfo=UTC),
        "title": "Firm - banking complaints",
        "body": "Firm received 42 banking complaints.",
        "firm_name": "Firm",
        "category": "Banking & Credit",
        "period_start": date(2025, 1, 1),
        "period_end": date(2025, 6, 30),
        "volume": 42,
        "provenance": build_provenance(),
    }
    payload.update(overrides)
    payload.setdefault("id", signal_id_for(str(payload["source_key"]), str(payload["external_id"])))
    return AggregateSignal.model_validate(payload)


def build_verbatim(**overrides: object) -> VerbatimSignal:
    payload: dict[str, object] = {
        "source_key": "reddit",
        "external_id": "t3_abc",
        "url": "https://example.org/post",
        "published_at": datetime(2026, 6, 1, tzinfo=UTC),
        "retrieved_at": datetime(2026, 7, 1, tzinfo=UTC),
        "title": None,
        "body": "My private bank lost my transfer.",
        "author_handle": "some_user",
        "provenance": build_provenance(),
    }
    payload.update(overrides)
    payload.setdefault("id", signal_id_for(str(payload["source_key"]), str(payload["external_id"])))
    return VerbatimSignal.model_validate(payload)
