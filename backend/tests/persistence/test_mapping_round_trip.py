"""Domain -> row values -> domain must be the identity, for both kinds."""

from datetime import UTC, date, datetime
from uuid import uuid4

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal, VerbatimSignal
from problemfinder.persistence.mapping import row_to_signal, signal_to_values
from problemfinder.persistence.orm import SignalRow

PROVENANCE = Provenance(
    raw_payload_sha256="b" * 64,
    adapter_version=2,
    ingestion_run_id=uuid4(),
    fetched_at=datetime(2026, 7, 2, tzinfo=UTC),
)


def test_aggregate_round_trip() -> None:
    signal = AggregateSignal(
        id=signal_id_for("fos_complaints", "x"),
        source_key="fos_complaints",
        external_id="x",
        url="https://example.org/x",
        published_at=datetime(2025, 10, 29, tzinfo=UTC),
        retrieved_at=datetime(2026, 7, 2, tzinfo=UTC),
        title="t",
        body="b",
        firm_name="Firm",
        category="Banking & Credit",
        extras={"business_group": "GROUP"},
        period_start=date(2025, 1, 1),
        period_end=date(2025, 6, 30),
        volume=10,
        upheld_share=0.25,
        provenance=PROVENANCE,
    )
    assert row_to_signal(SignalRow(**signal_to_values(signal))) == signal


def test_verbatim_round_trip() -> None:
    signal = VerbatimSignal(
        id=signal_id_for("reddit", "t3_1"),
        source_key="reddit",
        external_id="t3_1",
        url="https://example.org/t3_1",
        published_at=None,
        retrieved_at=datetime(2026, 7, 2, tzinfo=UTC),
        title=None,
        body="my adviser ghosted me",
        author_handle="user1",
        provenance=PROVENANCE,
    )
    assert row_to_signal(SignalRow(**signal_to_values(signal))) == signal
