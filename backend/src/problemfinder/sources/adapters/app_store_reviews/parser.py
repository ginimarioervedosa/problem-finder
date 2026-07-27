"""One archived feed page in, one record per review out. Pure, no I/O."""

import json
from collections.abc import Iterator

from pydantic import JsonValue

from problemfinder.sources.adapters.app_store_reviews.feed import (
    author_name,
    feed_entries,
    label,
    updated_at,
)
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_HINT_KEYS = ("app_id", "firm", "country")


def parse_review_page(raw: RawDocument) -> Iterator[ParsedRecord]:
    try:
        document = json.loads(raw.content)
    except (UnicodeDecodeError, ValueError) as error:
        raise SourceParseError(f"reviews feed page is not JSON: {error}") from error
    if not isinstance(document, dict) or "feed" not in document:
        raise SourceParseError("reviews feed page has no feed envelope")
    hints = raw.work_item.request_hints
    app_id = str(hints.get("app_id", ""))
    for entry in feed_entries(document):
        review_id = label(entry, "id")
        if review_id is None:
            continue
        fields: dict[str, JsonValue] = {
            "review_id": review_id,
            "title": label(entry, "title"),
            "content": label(entry, "content"),
            "author": author_name(entry),
            "rating": label(entry, "im:rating"),
            "app_version": label(entry, "im:version"),
            "vote_count": label(entry, "im:voteCount"),
            "updated": updated_at(entry),
            **{key: hints.get(key) for key in _HINT_KEYS},
        }
        yield ParsedRecord(external_id=f"{app_id}:{review_id}", fields=fields)
