"""The listing parser against a schema-faithful page, plus hostile inputs.

The fixture mirrors the Data API listing envelope exactly but is constructed,
not captured: unauthenticated listing access now returns 403, so a live page
needs the owner's OAuth credentials. Replace the fixture with a captured page
after the first real ingest run.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.reddit.parser import parse_listing
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "listing-new-page.json"


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="r/HENRYUK:new:start",
            url="https://oauth.reddit.com/r/HENRYUK/new?limit=100&raw_json=1",
            request_hints={"subreddit": "HENRYUK", "newest_created_utc": 1753380000.0},
        ),
        content=content,
        media_type="application/json",
        fetched_at=datetime(2026, 7, 25, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_listing(make_raw(FIXTURE.read_bytes())))


def test_one_record_per_post(records: list[ParsedRecord]) -> None:
    assert [record.external_id for record in records] == ["t3_1abcd01", "t3_1abcd02", "t3_1abcd03"]


def test_post_fields_are_extracted_verbatim(records: list[ParsedRecord]) -> None:
    first = records[0].fields
    assert first["title"] == "Private bank froze my account mid-completion"
    assert str(first["selftext"]).startswith("Exchanged on a property purchase")
    assert first["author"] == "throwaway_hnw"
    assert first["created_utc"] == 1753380000.0
    assert first["subreddit"] == "HENRYUK"
    assert first["score"] == 187
    assert first["num_comments"] == 64


def test_link_posts_carry_an_empty_selftext(records: list[ParsedRecord]) -> None:
    assert records[1].fields["selftext"] == ""


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_listing(make_raw(content)))
