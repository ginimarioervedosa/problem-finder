"""Wealth segment markers fire in priority order, verbatims only."""

from problemfinder.domain.dimensions import WealthSegment
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.passes.segment_inference import SegmentInferencePass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_aggregate, build_verbatim


def _segment(signal: ProblemSignal) -> WealthSegment | None:
    draft = EnrichmentDraft()
    SegmentInferencePass().apply(signal, draft)
    return draft.segment


def test_each_rule_fires_on_its_markers() -> None:
    cases = {
        "payments from his business account": WealthSegment.BUSINESS_OWNER,
        "a mortgage on a buy-to-let flat": WealthSegment.PROPERTY_INVESTOR,
        "money inherited from her late mother": WealthSegment.INHERITED_WEALTH,
        "transferred her pension into drawdown": WealthSegment.RETIREE,
    }
    for body, expected in cases.items():
        assert _segment(build_verbatim(body=body)) is expected, body


def test_priority_order_breaks_overlaps() -> None:
    body = "He paid his pension contributions from the business account."
    assert _segment(build_verbatim(body=body)) is WealthSegment.BUSINESS_OWNER


def test_no_marker_stays_none_rather_than_guessing() -> None:
    assert _segment(build_verbatim(body="A disputed card payment.")) is None


def test_aggregates_are_skipped() -> None:
    assert _segment(build_aggregate(body="pension complaints data")) is None
