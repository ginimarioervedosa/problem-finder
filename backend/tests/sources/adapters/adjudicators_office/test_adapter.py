"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("adjudicators_office")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("adjudicators_office").policy)


def test_cursor_fold_merges_previously_ingested_reports() -> None:
    source = registry.get("adjudicators_office")
    previous = Cursor(
        source_key="adjudicators_office",
        state={"ingested_reports": ["annual-report-2024"]},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [
        WorkItem(
            external_id="annual-report-2025",
            url="https://www.gov.uk/api/content/government/publications/x/y",
        )
    ]
    folded = source.cursor_after(previous, done)
    assert folded.state == {"ingested_reports": ["annual-report-2024", "annual-report-2025"]}
