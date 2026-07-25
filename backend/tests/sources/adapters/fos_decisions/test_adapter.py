"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("fos_decisions")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("fos_decisions").policy)


def test_cursor_fold_keeps_the_newest_date_ever_seen() -> None:
    source = registry.get("fos_decisions")
    previous = Cursor(
        source_key="fos_decisions",
        state={"latest_decision_date": "2025-05-01"},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [
        WorkItem(
            external_id="DRN-1",
            url="https://example.org/DRN-1.pdf",
            request_hints={"decision_date": "2025-03-01"},
        )
    ]
    folded = source.cursor_after(previous, done)
    assert folded.state == {"latest_decision_date": "2025-05-01"}
