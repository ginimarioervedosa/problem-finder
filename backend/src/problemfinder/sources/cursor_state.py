"""Cursor state for sources whose resume point is the set of items done.

Bulk-publication sources (a half-year data file, an annual report) resume by
remembering which publications they have ingested, not a high-water mark.
Both halves of that pattern live here so adapters declare only the state key.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.protocol import WorkItem


def ingested_keys(cursor: Cursor | None, state_key: str) -> set[str]:
    """External ids already ingested, out of the cursor's state."""
    if cursor is None:
        return set()
    keys = cursor.state.get(state_key)
    return {str(key) for key in keys} if isinstance(keys, list) else set()


def fold_ingested_keys(
    source_key: str, cursor: Cursor | None, state_key: str, done: Sequence[WorkItem]
) -> Cursor:
    """Merge finished work items into the cursor's set of ingested keys."""
    merged = ingested_keys(cursor, state_key) | {item.external_id for item in done}
    keys: list[JsonValue] = []
    keys.extend(sorted(merged))
    return Cursor(
        source_key=source_key,
        state={state_key: keys},
        updated_at=datetime.now(tz=UTC),
    )


def fold_newest_by_group(
    source_key: str,
    cursor: Cursor | None,
    state_key: str,
    done: Sequence[WorkItem],
    hints: tuple[str, str],
) -> Cursor:
    """Keep the greatest hint value ever seen per group, merging the old map.

    Incremental crawl sources resume from a per-group high-water mark: the
    newest post time per subreddit, the newest publication date per committee.
    `hints` names the (group, value) request hints on each done work item;
    values compare within their own kind (numbers as floats, strings as text).
    """
    group_hint, value_hint = hints
    previous = cursor.state.get(state_key) if cursor else None
    combined: dict[str, JsonValue] = dict(previous) if isinstance(previous, dict) else {}
    for item in done:
        group = str(item.request_hints.get(group_hint))
        seen = item.request_hints.get(value_hint)
        if isinstance(seen, bool) or not isinstance(seen, int | float | str) or seen == "":
            continue
        combined[group] = _newest(combined.get(group), seen)
    return Cursor(
        source_key=source_key,
        state={state_key: combined},
        updated_at=datetime.now(tz=UTC),
    )


def _newest(held: JsonValue | None, seen: float | str) -> JsonValue:
    if isinstance(seen, str):
        return max(held if isinstance(held, str) else "", seen)
    current = float(held) if isinstance(held, int | float) and not isinstance(held, bool) else 0.0
    return max(current, float(seen))
