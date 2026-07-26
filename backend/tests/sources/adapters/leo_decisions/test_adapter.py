"""The adapter registers itself and satisfies protocol and compliance gates."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.ingestion.compliance import check
from problemfinder.sources import registry
from problemfinder.sources.protocol import Source, WorkItem


def test_registered_under_its_key() -> None:
    source = registry.get("leo_decisions")
    assert isinstance(source, Source)
    assert source.version == 1


def test_policy_passes_the_compliance_gate() -> None:
    check(registry.get("leo_decisions").policy)


def test_cursor_fold_merges_previously_ingested_files() -> None:
    source = registry.get("leo_decisions")
    previous = Cursor(
        source_key="leo_decisions",
        state={"ingested_files": ["older-upload"]},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    done = [
        WorkItem(
            external_id="q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026",
            url="https://www.legalombudsman.org.uk/media/x/file.csv",
        )
    ]
    folded = source.cursor_after(previous, done)
    assert folded.state == {
        "ingested_files": [
            "older-upload",
            "q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026",
        ]
    }
