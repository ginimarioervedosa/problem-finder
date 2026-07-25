"""The discriminated signal union and the deterministic identity scheme."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from problemfinder.domain.identity import content_fingerprint, signal_id_for
from problemfinder.domain.signal import AggregateSignal, ProblemSignal, VerbatimSignal
from tests.support.builders import build_aggregate, build_provenance

SIGNAL_ADAPTER: TypeAdapter[VerbatimSignal | AggregateSignal] = TypeAdapter(ProblemSignal)


def test_discriminator_round_trips_aggregate() -> None:
    signal = build_aggregate()
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
            "provenance": build_provenance().model_dump(),
        }
    )
    assert isinstance(parsed, VerbatimSignal)
    assert parsed.author_handle == "some_user"


def test_signals_are_immutable() -> None:
    signal = build_aggregate()
    with pytest.raises(ValidationError):
        signal.body = "rewritten"  # type: ignore[misc]


def test_upheld_share_must_be_a_share() -> None:
    with pytest.raises(ValidationError):
        build_aggregate(upheld_share=1.5)


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValidationError):
        build_aggregate(retrieved_at=datetime(2026, 7, 1))


def test_identity_is_deterministic_and_distinct() -> None:
    assert signal_id_for("a", "1") == signal_id_for("a", "1")
    assert signal_id_for("a", "1") != signal_id_for("b", "1")
    assert content_fingerprint("a", "1", "x") != content_fingerprint("a", "1", "y")
