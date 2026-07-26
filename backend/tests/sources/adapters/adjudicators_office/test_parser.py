"""The case-study parser against a real trimmed report, plus hostile inputs."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.adjudicators_office.parser import parse_report
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "annual-report-2025.json"


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="annual-report-2025",
            url="https://www.gov.uk/api/content/government/publications/x/y",
            request_hints={
                "year": 2025,
                "page_url": "https://www.gov.uk/government/publications/x/y",
                "published_at": "2024-10-20T16:00:00+01:00",
            },
        ),
        content=content,
        media_type="application/json",
        fetched_at=datetime(2026, 7, 26, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_report(make_raw(FIXTURE.read_bytes())))


def test_each_case_study_yields_one_record(records: list[ParsedRecord]) -> None:
    assert [record.external_id for record in records] == [
        "annual-report-2025:case-study-01",
        "annual-report-2025:case-study-02",
    ]


def test_heading_metadata_is_extracted(records: list[ParsedRecord]) -> None:
    first = records[0]
    assert first.fields["decision"] == "Partially Upheld"
    assert first.fields["business_area"] == "Benefits and Credits"
    assert (
        first.fields["heading"]
        == "Case Study 1 Decision: Partially Upheld. Business Area: Benefits and Credits"
    )


def test_narrative_text_is_extracted_verbatim(records: list[ParsedRecord]) -> None:
    text = str(records[0].fields["text"])
    assert "recovery of tax credits overpayments" in text
    assert "Case Study" not in text  # headings stay out of the body


def test_discovery_hints_flow_into_the_record(records: list[ParsedRecord]) -> None:
    assert records[0].fields["year"] == 2025
    assert records[0].fields["page_url"] == "https://www.gov.uk/government/publications/x/y"
    assert records[0].fields["published_at"] == "2024-10-20T16:00:00+01:00"


def test_era_variant_headings_all_parse() -> None:
    body = (
        "<div><h3>Case Studies</h3><p>Intro prose, not a case study.</p>"
        "<h3>Case study 4: Enquiry procedures</h3><p>Older era.</p>"
        "<h3>Case Study</h3><p>Bare 2024-era heading.</p>"
        "<h3>Case Study 2, Decision: Fully Upheld</h3>"
        "<h4>Business Area: Benefits, Family and Customs</h4><p>2026 era.</p>"
        "<h2>Next section</h2><p>Never captured.</p></div>"
    )
    payload = json.dumps({"details": {"body": body}}).encode()
    records = list(parse_report(make_raw(payload)))
    assert [record.fields["decision"] for record in records] == [None, None, "Fully Upheld"]
    assert records[2].fields["business_area"] == "Benefits, Family and Customs"
    assert records[2].fields["text"] == "2026 era."
    assert all("Never captured" not in str(record.fields["text"]) for record in records)


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_report(make_raw(content)))
