"""ParsedRecord -> VerbatimSignal mapping, ids, and extras."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.signal import SignalKind
from problemfinder.sources.adapters.fos_decisions.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord
from tests.support.builders import build_provenance


def make_record(**overrides: object) -> ParsedRecord:
    fields: dict[str, object] = {
        "text": "The complaint. Mr C complains that his bank lost a transfer.",
        "drn": "DRN-4966044",
        "ombudsman": "Jane Example",
        "pdf_url": "https://www.financial-ombudsman.org.uk/decision/DRN-4966044.pdf",
        "decision_date": "2025-06-30",
        "business": "Revolut Ltd",
        "outcome": "Not upheld",
        "sector": "Banking and Payments",
        "page_url": "https://www.financial-ombudsman.org.uk/businesses/x/search",
    }
    fields.update(overrides)
    return ParsedRecord.model_validate({"external_id": "DRN-4966044", "fields": fields})


def test_maps_every_field_onto_the_verbatim_signal() -> None:
    signal = to_signal("fos_decisions", make_record(), build_provenance())
    assert signal.kind is SignalKind.VERBATIM
    assert signal.id == signal_id_for("fos_decisions", "DRN-4966044")
    assert signal.title == "Ombudsman decision DRN-4966044: Revolut Ltd (not upheld)"
    assert signal.body.startswith("The complaint.")
    assert signal.firm_name == "Revolut Ltd"
    assert signal.category == "Banking and Payments"
    assert signal.published_at == datetime(2025, 6, 30, tzinfo=UTC)
    assert str(signal.url).endswith("/decision/DRN-4966044.pdf")
    assert signal.author_handle is None
    assert signal.extras["outcome"] == "Not upheld"
    assert signal.extras["ombudsman"] == "Jane Example"


def test_identity_is_deterministic_for_the_same_decision() -> None:
    first = to_signal("fos_decisions", make_record(), build_provenance())
    second = to_signal("fos_decisions", make_record(), build_provenance())
    assert first.id == second.id


def test_missing_listing_metadata_degrades_gracefully() -> None:
    record = make_record(business=None, outcome=None, decision_date=None, sector=None)
    signal = to_signal("fos_decisions", record, build_provenance())
    assert signal.title == "Ombudsman decision DRN-4966044: unnamed business"
    assert signal.firm_name is None
    assert signal.category is None
    assert signal.published_at is None
