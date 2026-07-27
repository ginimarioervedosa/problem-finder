"""ParsedRecord -> VerbatimSignal mapping, ids, witnesses, extras."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.signal import SignalKind
from problemfinder.sources.adapters.committee_evidence.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord
from tests.support.builders import build_provenance


def make_record(**overrides: object) -> ParsedRecord:
    fields: dict[str, object] = {
        "text": "Written evidence submitted by UK Finance. Our members report...",
        "file_name": "TC0042.pdf",
        "committee_id": 158,
        "internal_reference": "TC0042",
        "publication_date": "2026-06-24T10:15:00",
        "business_title": "Bank of England Monetary Policy Reports",
        "witnesses": ["UK Finance", "Jane Example"],
        "page_url": "https://committees.parliament.uk/writtenevidence/167697/",
    }
    fields.update(overrides)
    return ParsedRecord.model_validate({"external_id": "167697", "fields": fields})


def test_maps_every_field_onto_the_verbatim_signal() -> None:
    signal = to_signal("committee_evidence", make_record(), build_provenance())
    assert signal.kind is SignalKind.VERBATIM
    assert signal.id == signal_id_for("committee_evidence", "167697")
    assert signal.title == "Written evidence TC0042: Bank of England Monetary Policy Reports"
    assert signal.body.startswith("Written evidence submitted by UK Finance.")
    assert signal.firm_name == "UK Finance"
    assert signal.author_handle == "UK Finance; Jane Example"
    assert signal.category == "Bank of England Monetary Policy Reports"
    assert signal.published_at == datetime(2026, 6, 24, 10, 15, tzinfo=UTC)
    assert str(signal.url) == "https://committees.parliament.uk/writtenevidence/167697/"
    assert signal.extras["internal_reference"] == "TC0042"
    assert signal.extras["committee_id"] == 158
    assert signal.extras["file_name"] == "TC0042.pdf"


def test_identity_is_deterministic_for_the_same_submission() -> None:
    first = to_signal("committee_evidence", make_record(), build_provenance())
    second = to_signal("committee_evidence", make_record(), build_provenance())
    assert first.id == second.id


def test_missing_metadata_degrades_gracefully() -> None:
    record = make_record(witnesses=[], business_title=None, publication_date=None, page_url=None)
    signal = to_signal("committee_evidence", record, build_provenance())
    assert signal.title == "Written evidence TC0042"
    assert signal.firm_name is None
    assert signal.author_handle is None
    assert signal.category is None
    assert signal.published_at is None
    assert str(signal.url).startswith("https://committees.parliament.uk")
