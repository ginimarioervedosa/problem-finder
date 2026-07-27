"""The workbook parser against the real H2 2025 file, plus hostile inputs."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from problemfinder.sources.adapters.fca_complaints_returns.parser import parse_workbook
from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError, WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "firm-level-complaints-data-2025-h2.xlsx"
PREFIXED_ERA_FIXTURE = (
    Path(__file__).parent / "fixtures" / "firm-level-complaints-data-2019-h2.xlsx"
)


def make_raw(content: bytes, period: str = "h2-2025") -> RawDocument:
    year = period.partition("-")[2]
    return RawDocument(
        work_item=WorkItem(
            external_id=period,
            url=f"https://www.fca.org.uk/publication/data/firm-level-complaints-data-{year}-h2.xlsx",
            request_hints={
                "period": period,
                "period_start": f"{year}-07-01",
                "period_end": f"{year}-12-31",
                "page_url": "https://www.fca.org.uk/data/complaints-data/firm-level",
            },
        ),
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        fetched_at=datetime(2026, 7, 27, tzinfo=UTC),
    )


@pytest.fixture(scope="module")
def records() -> list[ParsedRecord]:
    return list(parse_workbook(make_raw(FIXTURE.read_bytes())))


def test_yields_one_record_per_firm_product_with_volume(records: list[ParsedRecord]) -> None:
    assert len(records) > 400
    assert all(isinstance(r.fields["volume"], int) and r.fields["volume"] > 0 for r in records)


def test_known_row_parses_exactly(records: list[ParsedRecord]) -> None:
    accord = {
        str(r.fields["category"]): r
        for r in records
        if r.fields["firm_name"] == "Accord Mortgages Limited"
    }
    banking = accord["Banking and credit cards"]
    assert banking.external_id == "h2-2025:accord-mortgages-limited:banking-and-credit-cards"
    assert banking.fields["volume"] == 14
    assert banking.fields["upheld_share"] == pytest.approx(0.8333, abs=1e-4)
    assert banking.fields["closed"] == 12
    assert accord["Home finance"].fields["volume"] == 936


def test_firms_reporting_on_their_own_clock_carry_row_bounds(
    records: list[ParsedRecord],
) -> None:
    acromas = next(r for r in records if str(r.fields["firm_name"]).startswith("Acromas"))
    assert acromas.fields["row_period_start"] == "2025-02-01"
    assert acromas.fields["row_period_end"] == "2025-07-31"


def test_hints_flow_into_every_record(records: list[ParsedRecord]) -> None:
    sample = records[0].fields
    assert sample["period_start"] == "2025-07-01"
    assert sample["page_url"] == "https://www.fca.org.uk/data/complaints-data/firm-level"


def test_prefixed_sheet_era_parses_with_prose_reporting_periods() -> None:
    """2016 H2 to 2020: '(1.3) Opened' sheet names, headers under preamble rows."""
    records = list(parse_workbook(make_raw(PREFIXED_ERA_FIXTURE.read_bytes(), "h2-2019")))
    assert len(records) > 400
    [accord] = [
        r
        for r in records
        if r.fields["firm_name"] == "Accord Mortgages Limited"
        and r.fields["category"] == "Banking and credit cards"
    ]
    assert accord.fields["volume"] == 10
    assert accord.fields["upheld_share"] == pytest.approx(0.8889, abs=1e-4)
    assert accord.fields["closed"] == 9
    assert accord.fields["row_period_start"] == "2019-07-01"
    assert accord.fields["row_period_end"] == "2019-12-31"


@settings(max_examples=25, deadline=None)
@given(st.binary(min_size=0, max_size=2048))
def test_garbage_bytes_raise_only_parse_errors(content: bytes) -> None:
    with pytest.raises(SourceParseError):
        list(parse_workbook(make_raw(content)))
