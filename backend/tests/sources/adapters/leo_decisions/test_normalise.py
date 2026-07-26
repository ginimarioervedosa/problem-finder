"""ParsedRecord -> AggregateSignal mapping, quarter bounds, ids, extras."""

from datetime import UTC, date, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.signal import SignalKind
from problemfinder.sources.adapters.leo_decisions.normalise import to_signal
from problemfinder.sources.protocol import ParsedRecord
from tests.support.builders import build_provenance


def make_record(**overrides: object) -> ParsedRecord:
    fields: dict[str, object] = {
        "organisation": "Best Solicitors Limited",
        "organisation_type": "Firm SRA",
        "decisions_required": "1",
        "remedy_required": "1",
        "area_of_law": "Wills and Probate",
        "decision_date": "15/10/2025",
        "remedy_types": "To pay interest on monies held, To refund fees already paid",
        "remedy_amount": "£50,000 and above",
        "upheld_complaint_types": "Failure to release files or papers, Cost - Excessive",
        "evidence_of_poor_service": "Yes",
        "concluded_period": "2025-2026 Q 3",
        "complaint_handling_reasonable": "Yes",
        "page_url": "https://www.legalombudsman.org.uk/x/",
    }
    fields.update(overrides)
    return ParsedRecord.model_validate({"external_id": "D011954", "fields": fields})


def test_maps_every_field_onto_the_aggregate_signal() -> None:
    signal = to_signal("leo_decisions", make_record(), build_provenance())
    assert signal.kind is SignalKind.AGGREGATE
    assert signal.id == signal_id_for("leo_decisions", "D011954")
    assert signal.title == "Best Solicitors Limited: Wills and Probate decision D011954"
    assert "Upheld complaint types: Failure to release files or papers" in signal.body
    assert "Remedy directed: To pay interest" in signal.body
    assert signal.firm_name == "Best Solicitors Limited"
    assert signal.category == "Wills and Probate"
    assert signal.published_at == datetime(2025, 10, 15, tzinfo=UTC)
    assert signal.volume == 1
    assert signal.upheld_share == 1.0
    assert signal.extras["remedy_amount"] == "£50,000 and above"
    assert signal.extras["organisation_type"] == "Firm SRA"


def test_financial_year_quarter_bounds() -> None:
    q3 = to_signal("leo_decisions", make_record(), build_provenance())
    assert (q3.period_start, q3.period_end) == (date(2025, 10, 1), date(2025, 12, 31))
    q4 = make_record(concluded_period="2025-2026 Q 4")
    signal = to_signal("leo_decisions", q4, build_provenance())
    assert (signal.period_start, signal.period_end) == (date(2026, 1, 1), date(2026, 3, 31))


def test_unparseable_period_falls_back_to_the_decision_date() -> None:
    record = make_record(concluded_period=None)
    signal = to_signal("leo_decisions", record, build_provenance())
    assert signal.period_start == signal.period_end == date(2025, 10, 15)


def test_not_upheld_row_reads_as_no_remedy() -> None:
    record = make_record(
        remedy_required="0", remedy_types=None, remedy_amount=None, upheld_complaint_types=None
    )
    signal = to_signal("leo_decisions", record, build_provenance())
    assert signal.upheld_share == 0.0
    assert signal.body.endswith("No ombudsman remedy was required.")


def test_identity_is_deterministic_for_the_same_decision() -> None:
    first = to_signal("leo_decisions", make_record(), build_provenance())
    second = to_signal("leo_decisions", make_record(), build_provenance())
    assert first.id == second.id
