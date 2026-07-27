"""Field mapping, deterministic ids, and extras for App Store reviews."""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import JsonValue

from problemfinder.domain.provenance import Provenance
from problemfinder.sources.adapters.app_store_reviews.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord


def make_record(**overrides: JsonValue) -> ParsedRecord:
    fields: dict[str, JsonValue] = {
        "review_id": "14347220497",
        "title": "Best bank ever",
        "content": "The best bank ever. Only wish they did more.",
        "author": "Oznom2026@",
        "rating": "5",
        "app_version": "7.36.0",
        "vote_count": "0",
        "updated": "2026-07-25T10:17:29-07:00",
        "app_id": "1052238659",
        "firm": "Monzo",
        "country": "gb",
        **overrides,
    }
    return ParsedRecord(external_id="1052238659:14347220497", fields=fields)


def make_provenance() -> Provenance:
    return Provenance(
        raw_payload_sha256="0" * 64,
        adapter_version=1,
        ingestion_run_id=uuid4(),
        fetched_at=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
    )


def test_maps_the_review_onto_a_verbatim_signal() -> None:
    signal = to_signal("app_store_reviews", make_record(), make_provenance())
    assert signal.firm_name == "Monzo"
    assert signal.author_handle == "Oznom2026@"
    assert signal.title == "Monzo App Store review: Best bank ever"
    assert signal.body.startswith("The best bank ever")
    assert signal.extras["rating"] == 5
    assert signal.extras["app_version"] == "7.36.0"
    assert str(signal.url) == "https://apps.apple.com/gb/app/id1052238659?see-all=reviews"


def test_pacific_time_stamps_normalise_to_utc() -> None:
    signal = to_signal("app_store_reviews", make_record(), make_provenance())
    assert signal.published_at == datetime(2026, 7, 25, 17, 17, 29, tzinfo=UTC)


def test_ids_are_deterministic_for_the_same_review() -> None:
    one = to_signal("app_store_reviews", make_record(), make_provenance())
    two = to_signal("app_store_reviews", make_record(), make_provenance())
    assert one.id == two.id


def test_missing_optionals_degrade_to_none_not_crashes() -> None:
    record = make_record(rating=None, updated=None, title=None, author=None)
    signal = to_signal("app_store_reviews", record, make_provenance())
    assert signal.extras["rating"] is None
    assert signal.published_at is None
    assert signal.title is None
    assert signal.author_handle is None
