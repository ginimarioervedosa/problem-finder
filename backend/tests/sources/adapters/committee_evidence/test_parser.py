"""The evidence parser against real API envelopes, plus hostile inputs."""

import base64
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.committee_evidence.parser import parse_evidence
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURES = Path(__file__).parent / "fixtures"


def make_raw(content: bytes, external_id: str = "165251") -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id=external_id,
            url=f"https://committees-api.parliament.uk/api/WrittenEvidence/{external_id}/Document/OriginalFormat",
            request_hints={
                "committee_id": 158,
                "internal_reference": "SLTG0177",
                "publication_date": "2026-05-28T09:30:00",
                "business_title": "Student loans and taxation of graduates",
                "witnesses": ["Mr Vincent Murtagh"],
                "page_url": f"https://committees.parliament.uk/writtenevidence/{external_id}/",
            },
        ),
        content=content,
        media_type="application/json",
        fetched_at=datetime(2026, 7, 26, tzinfo=UTC),
    )


def parse_fixture(name: str) -> ParsedRecord:
    [record] = list(parse_evidence(make_raw((FIXTURES / name).read_bytes())))
    return record


def test_docx_submission_text_is_extracted() -> None:
    record = parse_fixture("SLTG0177-docx-envelope.json")
    assert record.external_id == "165251"
    assert record.fields["file_name"] == "SLTG0177.docx"
    text = str(record.fields["text"])
    assert "Written evidence submitted by Mr Vincent Murtagh" in text
    assert "Part A is a suggestion for a new system" in text


def test_pdf_submission_text_is_extracted() -> None:
    record = parse_fixture("SLTG0151-pdf-envelope.json")
    text = str(record.fields["text"])
    assert "Written evidence submitted by Anonymous" in text
    assert "Student Loans and Taxation of Graduates" in text


def test_discovery_hints_flow_into_the_record() -> None:
    record = parse_fixture("SLTG0177-docx-envelope.json")
    assert record.fields["internal_reference"] == "SLTG0177"
    assert record.fields["business_title"] == "Student loans and taxation of graduates"
    assert record.fields["witnesses"] == ["Mr Vincent Murtagh"]
    assert record.fields["committee_id"] == 158


def test_unsupported_formats_are_a_parse_error() -> None:
    envelope = json.dumps(
        {"data": base64.b64encode(b"\x00\x01binary").decode(), "fileName": "evidence.xls"}
    ).encode()
    with pytest.raises(SourceParseError, match="unsupported evidence format"):
        list(parse_evidence(make_raw(envelope)))


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_evidence(make_raw(content)))
