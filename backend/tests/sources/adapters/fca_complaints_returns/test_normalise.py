"""Field mapping, deterministic ids, and extras for the FCA returns source."""

from datetime import UTC, date, datetime
from uuid import uuid4

from pydantic import JsonValue

from problemfinder.domain.provenance import Provenance
from problemfinder.sources.adapters.fca_complaints_returns.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord


def make_record(**overrides: JsonValue) -> ParsedRecord:
    fields: dict[str, JsonValue] = {
        "firm_name": "Accord Mortgages Limited",
        "firm_group": "YORKSHIRE BUILDING SOCIETY",
        "joint_reporting": "no",
        "reporting_period": "2025-07-01 to 2025-12-31",
        "category": "Home finance",
        "volume": 936,
        "upheld_share": 0.6363,
        "closed": 880,
        "row_period_start": "2025-07-01",
        "row_period_end": "2025-12-31",
        "period": "h2-2025",
        "period_start": "2025-07-01",
        "period_end": "2025-12-31",
        "page_url": "https://www.fca.org.uk/data/complaints-data/firm-level",
        **overrides,
    }
    return ParsedRecord(external_id="h2-2025:accord-mortgages-limited:home-finance", fields=fields)


def make_provenance() -> Provenance:
    return Provenance(
        raw_payload_sha256="0" * 64,
        adapter_version=1,
        ingestion_run_id=uuid4(),
        fetched_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
    )


def test_maps_the_return_onto_an_aggregate_signal() -> None:
    signal = to_signal("fca_complaints_returns", make_record(), make_provenance())
    assert signal.firm_name == "Accord Mortgages Limited"
    assert signal.category == "Home finance"
    assert signal.volume == 936
    assert signal.upheld_share == 0.6363
    assert signal.denominator == 880
    assert signal.period_start == date(2025, 7, 1)
    assert "936 Home finance complaints opened" in signal.body
    assert "64% of the complaints it closed" in signal.body
    assert signal.extras["firm_group"] == "YORKSHIRE BUILDING SOCIETY"


def test_ids_are_deterministic_for_the_same_evidence() -> None:
    one = to_signal("fca_complaints_returns", make_record(), make_provenance())
    two = to_signal("fca_complaints_returns", make_record(), make_provenance())
    assert one.id == two.id


def test_row_period_wins_over_the_release_half_year() -> None:
    record = make_record(row_period_start="2025-02-01", row_period_end="2025-07-31")
    signal = to_signal("fca_complaints_returns", record, make_provenance())
    assert signal.period_start == date(2025, 2, 1)
    assert signal.period_end == date(2025, 7, 31)


def test_release_bounds_apply_when_the_row_period_is_unreadable() -> None:
    record = make_record(row_period_start=None, row_period_end=None)
    signal = to_signal("fca_complaints_returns", record, make_provenance())
    assert signal.period_start == date(2025, 7, 1)
    assert signal.period_end == date(2025, 12, 31)


def test_no_group_becomes_null_and_missing_upheld_stays_unstated() -> None:
    record = make_record(firm_group="NO GROUP", upheld_share=None)
    signal = to_signal("fca_complaints_returns", record, make_provenance())
    assert signal.extras["firm_group"] is None
    assert signal.upheld_share is None
    assert "upheld" not in signal.body
