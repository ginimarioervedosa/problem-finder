"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("committee_evidence")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("committee_evidence").policy)


def test_cursor_fold_keeps_the_newest_publication_date_per_committee() -> None:
    source = registry.get("committee_evidence")
    previous = Cursor(
        source_key="committee_evidence",
        state={
            "newest_publication_date": {"158": "2026-05-01T00:00:00", "159": "2026-06-01T00:00:00"}
        },
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [
        WorkItem(
            external_id="167697",
            url="https://committees-api.parliament.uk/api/WrittenEvidence/167697/Document/OriginalFormat",
            request_hints={"committee_id": 158, "publication_date": "2026-06-24T10:15:00"},
        ),
        WorkItem(
            external_id="165375",
            url="https://committees-api.parliament.uk/api/WrittenEvidence/165375/Document/OriginalFormat",
            request_hints={"committee_id": 158, "publication_date": "2026-05-28T09:30:00"},
        ),
    ]
    folded = source.cursor_after(previous, done)
    assert folded.state == {
        "newest_publication_date": {"158": "2026-06-24T10:15:00", "159": "2026-06-01T00:00:00"}
    }
