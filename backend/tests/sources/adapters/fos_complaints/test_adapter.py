"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("fos_complaints")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("fos_complaints").policy)


def test_cursor_fold_merges_previously_ingested_periods() -> None:
    source = registry.get("fos_complaints")
    previous = Cursor(
        source_key="fos_complaints",
        state={"ingested_periods": ["h1-2024"]},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [WorkItem(external_id="h2-2024", url="https://example.org/h2-2024.xlsx")]
    folded = source.cursor_after(previous, done)
    assert folded.state == {"ingested_periods": ["h1-2024", "h2-2024"]}
