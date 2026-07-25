"""Fold per-subreddit newest-post times into the resume cursor."""

from collections.abc import Sequence
from datetime import UTC, datetime

from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.protocol import WorkItem


def fold_cursor(source_key: str, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
    """Keep the newest created_utc ever seen per subreddit, merging the old map."""
    previous = cursor.state.get("newest_created_utc") if cursor else None
    combined: dict[str, JsonValue] = dict(previous) if isinstance(previous, dict) else {}
    for item in done:
        subreddit = str(item.request_hints.get("subreddit"))
        seen = item.request_hints.get("newest_created_utc")
        if isinstance(seen, bool) or not isinstance(seen, int | float):
            continue
        held = combined.get(subreddit)
        current = float(held) if isinstance(held, int | float) else 0.0
        combined[subreddit] = max(current, float(seen))
    return Cursor(
        source_key=source_key,
        state={"newest_created_utc": combined},
        updated_at=datetime.now(tz=UTC),
    )
