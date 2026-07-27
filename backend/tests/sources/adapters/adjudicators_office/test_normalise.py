"""ParsedRecord -> VerbatimSignal mapping, ids, and extras."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.signal import SignalKind
from problemfinder.sources.adapters.adjudicators_office.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord
from tests.support.builders import build_provenance


def make_record(**overrides: object) -> ParsedRecord:
    fields: dict[str, object] = {
        "heading": "Case Study 1 Decision: Partially Upheld. Business Area: Benefits and Credits",
        "text": "The customer complained that HMRC recovered a tax credits overpayment.",
        "decision": "Partially Upheld",
        "business_area": "Benefits and Credits",
        "year": 2025,
        "page_url": "https://www.gov.uk/government/publications/x/y",
        "published_at": "2024-10-20T16:00:00+01:00",
    }
    fields.update(overrides)
    return ParsedRecord.model_validate(
        {"external_id": "annual-report-2025:case-study-01", "fields": fields}
    )


def test_maps_every_field_onto_the_verbatim_signal() -> None:
    signal = to_signal("adjudicators_office", make_record(), build_provenance())
    assert signal.kind is SignalKind.VERBATIM
    assert signal.id == signal_id_for("adjudicators_office", "annual-report-2025:case-study-01")
    assert signal.title == (
        "Case Study 1 Decision: Partially Upheld. Business Area: Benefits and Credits"
    )
    assert signal.body.startswith("The customer complained")
    assert signal.firm_name == "HMRC"
    assert signal.category == "Benefits and Credits"
    assert signal.published_at == datetime(2024, 10, 20, 15, 0, tzinfo=UTC)
    assert str(signal.url) == "https://www.gov.uk/government/publications/x/y"
    assert signal.author_handle is None
    assert signal.extras["outcome"] == "Partially Upheld"
    assert signal.extras["report_year"] == 2025


def test_identity_is_deterministic_for_the_same_case_study() -> None:
    first = to_signal("adjudicators_office", make_record(), build_provenance())
    second = to_signal("adjudicators_office", make_record(), build_provenance())
    assert first.id == second.id


def test_department_is_the_first_named_in_the_narrative() -> None:
    voa = make_record(
        text="The Valuation Office Agency banded the property; HMRC was not involved."
    )
    assert to_signal("adjudicators_office", voa, build_provenance()).firm_name == (
        "Valuation Office Agency"
    )
    unnamed = make_record(text="The department misplaced the customer's letter.")
    assert to_signal("adjudicators_office", unnamed, build_provenance()).firm_name is None


def test_missing_heading_metadata_degrades_gracefully() -> None:
    record = make_record(decision=None, business_area=None, published_at=None, page_url=None)
    signal = to_signal("adjudicators_office", record, build_provenance())
    assert signal.category is None
    assert signal.published_at is None
    assert signal.extras["outcome"] is None
    assert str(signal.url).endswith("/organisations/the-adjudicator-s-office")
