"""One archived listing page in, one record per post out. Pure, no I/O."""

import json
from collections.abc import Iterator

from pydantic import JsonValue

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_POST_FIELDS = (
    "title",
    "selftext",
    "author",
    "created_utc",
    "permalink",
    "subreddit",
    "score",
    "num_comments",
)


def parse_listing(raw: RawDocument) -> Iterator[ParsedRecord]:
    try:
        children = json.loads(raw.content)["data"]["children"]
    except (ValueError, KeyError, TypeError) as exc:
        msg = f"not a reddit listing: {exc}"
        raise SourceParseError(msg) from exc
    if not isinstance(children, list):
        raise SourceParseError("not a reddit listing: children is not a list")
    for child in children:
        yield _record(child)


def _record(child: object) -> ParsedRecord:
    data = child.get("data") if isinstance(child, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get("name"), str):
        raise SourceParseError("listing child without a post data object")
    fields: dict[str, JsonValue] = {key: data.get(key) for key in _POST_FIELDS}
    return ParsedRecord(external_id=data["name"], fields=fields)
