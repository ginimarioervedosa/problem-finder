"""Seen-set cursor state: reading ingested keys and folding finished work."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.cursor_state import fold_ingested_keys, ingested_keys
from problemfinder.sources.protocol import WorkItem


def make_cursor(state: dict[str, object]) -> Cursor:
    return Cursor.model_validate(
        {"source_key": "example", "state": state, "updated_at": datetime(2026, 7, 1, tzinfo=UTC)}
    )


def test_no_cursor_means_nothing_ingested() -> None:
    assert ingested_keys(None, "ingested_reports") == set()


def test_malformed_state_degrades_to_empty() -> None:
    assert ingested_keys(make_cursor({"ingested_reports": "oops"}), "ingested_reports") == set()


def test_fold_merges_done_items_into_sorted_state() -> None:
    cursor = make_cursor({"ingested_reports": ["b"]})
    done = [
        WorkItem(external_id="a", url="https://example.org/a"),
        WorkItem(external_id="c", url="https://example.org/c"),
    ]
    folded = fold_ingested_keys("example", cursor, "ingested_reports", done)
    assert folded.source_key == "example"
    assert folded.state == {"ingested_reports": ["a", "b", "c"]}
    assert ingested_keys(folded, "ingested_reports") == {"a", "b", "c"}
