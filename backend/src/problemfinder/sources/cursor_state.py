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
