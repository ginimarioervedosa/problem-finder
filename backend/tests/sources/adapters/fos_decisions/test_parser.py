"""The decision parser against a real published PDF, plus hostile inputs."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.fos_decisions.parser import parse_decision
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "DRN-5603795.pdf"


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="DRN-5603795",
            url="https://www.financial-ombudsman.org.uk/decision/DRN-5603795.pdf",
            request_hints={
                "decision_date": "2025-06-25",
                "business": "Handelsbanken plc",
                "outcome": "Not upheld",
                "sector": "Banking and Payments",
                "page_url": "https://www.financial-ombudsman.org.uk/businesses/x/search",
            },
        ),
        content=content,
        media_type="application/pdf",
        fetched_at=datetime(2026, 7, 25, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def record() -> ParsedRecord:
    [only] = list(parse_decision(make_raw(FIXTURE.read_bytes())))
    return only


def test_one_decision_yields_one_record(record: ParsedRecord) -> None:
    assert record.external_id == "DRN-5603795"
    assert record.fields["drn"] == "DRN-5603795"


def test_write_up_text_is_extracted_verbatim(record: ParsedRecord) -> None:
    text = str(record.fields["text"])
    assert "Mrs H complains" in text
    assert "uphold this complaint" in text
    assert "My final decision" in text


def test_ombudsman_name_is_extracted(record: ParsedRecord) -> None:
    assert record.fields["ombudsman"] == "Esther Absalom-Gough"


def test_listing_hints_flow_into_the_record(record: ParsedRecord) -> None:
    assert record.fields["business"] == "Handelsbanken plc"
    assert record.fields["outcome"] == "Not upheld"
    assert record.fields["decision_date"] == "2025-06-25"
    assert (
        record.fields["pdf_url"]
        == "https://www.financial-ombudsman.org.uk/decision/DRN-5603795.pdf"
    )


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_decision(make_raw(content)))
