"""The discriminated signal union and the deterministic identity scheme."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from problemfinder.domain.identity import content_fingerprint, signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal, ProblemSignal, VerbatimSignal

SIGNAL_ADAPTER: TypeAdapter[VerbatimSignal | AggregateSignal] = TypeAdapter(ProblemSignal)


def make_provenance() -> Provenance:
    return Provenance(
        raw_payload_sha256="a" * 64,
        adapter_version=1,
        ingestion_run_id=uuid4(),
        fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def make_aggregate(**overrides: object) -> AggregateSignal:
    payload: dict[str, object] = {
        "id": signal_id_for("fos_complaints", "h1-2025:firm:banking"),
        "source_key": "fos_complaints",
        "external_id": "h1-2025:firm:banking",
        "url": "https://example.org/data",
        "published_at": None,
        "retrieved_at": datetime(2026, 7, 1, tzinfo=UTC),
        "title": "Firm - banking complaints",
        "body": "Firm received 42 banking complaints.",
        "period_start": date(2025, 1, 1),
        "period_end": date(2025, 6, 30),
        "volume": 42,
        "provenance": make_provenance(),
    }
    payload.update(overrides)
    return AggregateSignal.model_validate(payload)


def test_discriminator_round_trips_aggregate() -> None:
    signal = make_aggregate()
    parsed = SIGNAL_ADAPTER.validate_json(signal.model_dump_json())
    assert isinstance(parsed, AggregateSignal)
    assert parsed == signal


def test_discriminator_selects_verbatim_from_plain_dict() -> None:
    parsed = SIGNAL_ADAPTER.validate_python(
        {
            "kind": "verbatim",
            "id": str(uuid4()),
            "source_key": "reddit",
            "external_id": "t3_abc",
            "url": "https://example.org/post",
            "published_at": "2026-06-01T12:00:00Z",
            "retrieved_at": "2026-07-01T12:00:00Z",
            "title": None,
            "body": "My private bank lost my transfer.",
            "author_handle": "some_user",
            "provenance": make_provenance().model_dump(),
        }
    )
    assert isinstance(parsed, VerbatimSignal)
    assert parsed.author_handle == "some_user"


def test_signals_are_immutable() -> None:
    signal = make_aggregate()
    with pytest.raises(ValidationError):
        signal.body = "rewritten"  # type: ignore[misc]


def test_upheld_share_must_be_a_share() -> None:
    with pytest.raises(ValidationError):
        make_aggregate(upheld_share=1.5)


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValidationError):
        make_aggregate(retrieved_at=datetime(2026, 7, 1))


def test_identity_is_deterministic_and_distinct() -> None:
    assert signal_id_for("a", "1") == signal_id_for("a", "1")
    assert signal_id_for("a", "1") != signal_id_for("b", "1")
    assert content_fingerprint("a", "1", "x") != content_fingerprint("a", "1", "y")
