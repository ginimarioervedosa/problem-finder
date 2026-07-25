"""Record -> AggregateSignal mapping is deterministic and lossless."""

from datetime import UTC, date, datetime
from uuid import uuid4

from problemfinder.domain.provenance import Provenance
from problemfinder.sources.adapters.fos_complaints.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord

PROVENANCE = Provenance(
    raw_payload_sha256="c" * 64,
    adapter_version=1,
    ingestion_run_id=uuid4(),
    fetched_at=datetime(2026, 7, 25, 9, 0, tzinfo=UTC),
)

RECORD = ParsedRecord(
    external_id="h1-2025:accord-mortgages-limited:mortgages-home-finance",
    fields={
        "business_name": "Accord Mortgages Limited",
        "business_group": "YORKSHIRE",
        "category": "Mortgages & Home Finance",
        "volume": 29,
        "upheld_share": 0.11627907,
        "total_new_cases": 30,
        "period": "h1-2025",
        "period_start": "2025-01-01",
        "period_end": "2025-06-30",
        "page_url": "https://www.financial-ombudsman.org.uk/data-insight/x",
        "published_at": "2025-10-29T00:00:00+00:00",
    },
)


def test_maps_the_full_record() -> None:
    signal = to_signal("fos_complaints", RECORD, PROVENANCE)
    assert signal.firm_name == "Accord Mortgages Limited"
    assert signal.category == "Mortgages & Home Finance"
    assert signal.volume == 29
    assert signal.upheld_share is not None
    assert signal.period_start == date(2025, 1, 1)
    assert signal.period_end == date(2025, 6, 30)
    assert signal.published_at == datetime(2025, 10, 29, tzinfo=UTC)
    assert signal.retrieved_at == PROVENANCE.fetched_at
    assert signal.extras["business_group"] == "YORKSHIRE"
    assert "29 new Mortgages & Home Finance complaints" in signal.body
    assert "12%" in signal.body


def test_identity_is_stable_across_reparse() -> None:
    first = to_signal("fos_complaints", RECORD, PROVENANCE)
    second = to_signal("fos_complaints", RECORD, PROVENANCE)
    assert first.id == second.id


def test_no_group_is_normalised_to_none() -> None:
    record = RECORD.model_copy(update={"fields": {**RECORD.fields, "business_group": "No Group"}})
    signal = to_signal("fos_complaints", record, PROVENANCE)
    assert signal.extras["business_group"] is None


def test_era_variant_categories_share_one_canonical_label() -> None:
    for raw in (
        "General Insurance / Pure Protection (Includes PPI)",
        "General Insurance / Pure Protection (including PPI)",
        "General Insurance / Pure Protection",
    ):
        record = RECORD.model_copy(update={"fields": {**RECORD.fields, "category": raw}})
        signal = to_signal("fos_complaints", record, PROVENANCE)
        assert signal.category == "General Insurance / Pure Protection"
        assert signal.extras["source_category"] == raw
