"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("fca_complaints_returns")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("fca_complaints_returns").policy)


def test_policy_records_the_owner_risk_acceptance() -> None:
    notes = registry.get("fca_complaints_returns").policy.terms_notes
    assert "accepted by the owner on 2026-07-27" in notes
    assert "4.8(iii)" in notes


def test_cursor_fold_merges_previously_ingested_periods() -> None:
    source = registry.get("fca_complaints_returns")
    previous = Cursor(
        source_key="fca_complaints_returns",
        state={"ingested_periods": ["h2-2016"]},
        updated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    done = [WorkItem(external_id="h1-2017", url="https://example.org/h1-2017.xlsx")]
    folded = source.cursor_after(previous, done)
    assert folded.state == {"ingested_periods": ["h1-2017", "h2-2016"]}
