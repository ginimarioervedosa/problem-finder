"""The feed-page parser against a real Monzo page, plus hostile inputs."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.app_store_reviews.parser import parse_review_page
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "customerreviews-page-1.json"


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="gb:1052238659:page-1",
            url=(
                "https://itunes.apple.com/gb/rss/customerreviews"
                "/id=1052238659/sortby=mostrecent/page=1/json"
            ),
            request_hints={
                "app_id": "1052238659",
                "firm": "Monzo",
                "country": "gb",
                "newest_updated": "2026-07-25T17:17:29+00:00",
            },
        ),
        content=content,
        media_type="application/json",
        fetched_at=datetime(2026, 7, 27, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_review_page(make_raw(FIXTURE.read_bytes())))


def test_yields_one_record_per_review(records: list[ParsedRecord]) -> None:
    assert len(records) == 4
    assert [r.external_id for r in records][:2] == [
        "1052238659:14347220497",
        "1052238659:14347153757",
    ]


def test_known_review_parses_exactly(records: list[ParsedRecord]) -> None:
    review = records[0].fields
    assert review["title"] == "Best bank ever"
    assert review["rating"] == "5"
    assert review["author"] == "Oznom2026@"
    assert review["updated"] == "2026-07-25T10:17:29-07:00"
    assert isinstance(review["content"], str) and review["content"].startswith("The best bank")


def test_hints_flow_into_every_record(records: list[ParsedRecord]) -> None:
    assert all(r.fields["firm"] == "Monzo" for r in records)
    assert all(r.fields["country"] == "gb" for r in records)


def test_single_entry_pages_and_empty_pages_parse() -> None:
    document = json.loads(FIXTURE.read_bytes())
    document["feed"]["entry"] = document["feed"]["entry"][0]  # bare object, not a list
    [only] = list(parse_review_page(make_raw(json.dumps(document).encode())))
    assert only.external_id == "1052238659:14347220497"
    del document["feed"]["entry"]  # a page past the last review has no entries
    assert list(parse_review_page(make_raw(json.dumps(document).encode()))) == []


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_review_page(make_raw(content)))
