"""Shared cursor state: seen-set folds and newest-per-group high-water folds."""

from datetime import UTC, datetime

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.cursor_state import (
    fold_ingested_keys,
    fold_newest_by_group,
    ingested_keys,
)
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


def _item(group: object, value: object) -> WorkItem:
    return WorkItem(
        external_id="x",
        url="https://example.org/x",
        request_hints={"group": group, "value": value},
    )


def test_newest_by_group_keeps_the_greatest_string_value() -> None:
    cursor = make_cursor({"marks": {"a": "2026-05-01", "b": "2026-06-01"}})
    done = [_item("a", "2026-06-24"), _item("a", "2026-03-01")]
    folded = fold_newest_by_group("example", cursor, "marks", done, ("group", "value"))
    assert folded.state == {"marks": {"a": "2026-06-24", "b": "2026-06-01"}}


def test_newest_by_group_keeps_the_greatest_numeric_value() -> None:
    done = [_item("r/example", 100.0), _item("r/example", 50)]
    folded = fold_newest_by_group("example", None, "marks", done, ("group", "value"))
    assert folded.state == {"marks": {"r/example": 100.0}}


def test_newest_by_group_ignores_missing_or_empty_values() -> None:
    done = [_item("a", None), _item("a", ""), _item("a", True)]
    folded = fold_newest_by_group("example", None, "marks", done, ("group", "value"))
    assert folded.state == {"marks": {}}
