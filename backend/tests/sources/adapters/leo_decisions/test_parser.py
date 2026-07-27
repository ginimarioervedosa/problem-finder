"""The decision-data parser against a real trimmed CSV, plus hostile inputs."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.leo_decisions.parser import parse_decision_data
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "decision-data.csv"
PAGE_URL = (
    "https://www.legalombudsman.org.uk/information-centre/data-centre/ombudsman-decision-data/"
)


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026",
            url="https://www.legalombudsman.org.uk/media/x/decision-data.csv",
            request_hints={"page_url": PAGE_URL},
        ),
        content=content,
        media_type="text/csv",
        fetched_at=datetime(2026, 7, 26, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_decision_data(make_raw(FIXTURE.read_bytes())))


def test_each_row_yields_one_record_keyed_by_decision_id(records: list[ParsedRecord]) -> None:
    assert [record.external_id for record in records] == [
        "D011001",
        "D011596",
        "D011954",
        "D012309",
        "D012317",
        "D012270",
    ]


def test_columns_map_onto_snake_case_fields(records: list[ParsedRecord]) -> None:
    first = records[0]
    assert first.fields["organisation"] == "Mr Simon David Burch of St Ive's Chambers"
    assert first.fields["organisation_type"] == "Barrister of X Chambers"
    assert first.fields["area_of_law"] == "Litigation"
    assert first.fields["decision_date"] == "25/11/2024"
    assert first.fields["remedy_required"] == "1"
    assert first.fields["concluded_period"] == "2024-2025 Q 3"
    assert first.fields["page_url"] == PAGE_URL


def test_not_applicable_markers_degrade_to_none(records: list[ParsedRecord]) -> None:
    not_upheld = records[-1]
    assert not_upheld.fields["remedy_required"] == "0"
    assert not_upheld.fields["remedy_types"] is None
    assert not_upheld.fields["remedy_amount"] is None
    assert not_upheld.fields["upheld_complaint_types"] is None


def test_missing_columns_are_a_parse_error() -> None:
    with pytest.raises(SourceParseError, match="expected columns"):
        list(parse_decision_data(make_raw(b"Organisation,ID\nX,D1\n")))


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_decision_data(make_raw(content)))
