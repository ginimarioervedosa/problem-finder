"""The workbook parser against the real H1 2025 file, plus hostile inputs."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.fos_complaints.parser import (
    _is_totals_or_footnote,
    parse_workbook,
)
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "business-complaints-data-h1-2025.xlsx"


def make_raw(content: bytes) -> RawDocument:
    return RawDocument(
        work_item=WorkItem(
            external_id="h1-2025",
            url="https://www.financial-ombudsman.org.uk/files/324668/x.xlsx",
            request_hints={
                "period": "h1-2025",
                "period_start": "2025-01-01",
                "period_end": "2025-06-30",
                "page_url": "https://www.financial-ombudsman.org.uk/data-insight/x",
                "published_at": "2025-10-29T00:00:00+00:00",
            },
        ),
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        fetched_at=datetime(2026, 7, 25, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_workbook(make_raw(FIXTURE.read_bytes())))


def test_yields_one_record_per_business_category_with_volume(records: list[ParsedRecord]) -> None:
    assert len(records) > 300
    assert all(isinstance(r.fields["volume"], int) and r.fields["volume"] > 0 for r in records)


def test_known_row_parses_exactly(records: list[ParsedRecord]) -> None:
    [aa] = [r for r in records if str(r.fields["business_name"]).startswith("AA Underwriting")]
    expected_id = (
        "h1-2025:aa-underwriting-insurance-company-limited:"
        "general-insurance-pure-protection-includes-ppi"
    )
    assert aa.external_id == expected_id
    assert aa.fields["volume"] == 140
    assert aa.fields["category"] == "General Insurance / Pure Protection (Includes PPI)"
    upheld = aa.fields["upheld_share"]
    assert isinstance(upheld, float)
    assert upheld == pytest.approx(0.4569, abs=1e-3)


def test_multi_category_business_splits_into_records(records: list[ParsedRecord]) -> None:
    accord = [r for r in records if r.fields["business_name"] == "Accord Mortgages Limited"]
    volumes = {r.fields["category"]: r.fields["volume"] for r in accord}
    assert volumes["Mortgages & Home Finance"] == 29
    assert volumes["General Insurance / Pure Protection (Includes PPI)"] == 1


def test_totals_and_footnote_rows_are_excluded(records: list[ParsedRecord]) -> None:
    names = {str(r.fields["business_name"]).lower() for r in records}
    assert not any("total number of complaints" in name for name in names)
    assert not any(name.startswith("*") for name in names)


@pytest.mark.parametrize(
    "label",
    ["TOTALS", "Total", "Total (45/ 45 Threshold)", "Total of above", "Totals of the above"],
)
def test_every_observed_totals_label_is_excluded(label: str) -> None:
    assert _is_totals_or_footnote(label, None)


def test_a_real_firm_named_total_is_kept() -> None:
    assert not _is_totals_or_footnote("Total Insurance Services Ltd", "No Group")


def test_hints_flow_into_every_record(records: list[ParsedRecord]) -> None:
    sample = records[0].fields
    assert sample["period_start"] == "2025-01-01"
    assert sample["page_url"] == "https://www.financial-ombudsman.org.uk/data-insight/x"


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_workbook(make_raw(content)))


LEGACY_FIXTURE = Path(__file__).parent / "fixtures" / "business-complaints-data-h1-2013.xlsx"


def test_legacy_workbook_era_parses_with_positional_upheld_shares() -> None:
    """2009-2020 files: 'New/Resolved complaints' sheets, three-row resolved header."""
    records = list(parse_workbook(make_raw(LEGACY_FIXTURE.read_bytes())))
    assert len(records) > 300
    categories = {str(record.fields["category"]) for record in records}
    assert "PPI" in categories  # separate category in the legacy era
    with_upheld = [r for r in records if r.fields["upheld_share"] is not None]
    assert len(with_upheld) > 100
    assert all(
        isinstance(r.fields["upheld_share"], float) and 0 <= r.fields["upheld_share"] <= 1
        for r in with_upheld
    )
