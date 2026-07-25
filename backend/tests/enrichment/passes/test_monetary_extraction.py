"""Sterling extraction: the largest credible amount, quantised to pence."""

from decimal import Decimal

from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.passes.monetary_extraction import MonetaryExtractionPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_aggregate, build_verbatim


def _extracted(signal: ProblemSignal) -> EnrichmentDraft:
    draft = EnrichmentDraft()
    MonetaryExtractionPass().apply(signal, draft)
    return draft


def test_largest_amount_wins_and_is_quantised() -> None:
    draft = _extracted(build_verbatim(body="She paid £1,250.50 in fees and lost £45,000."))
    assert draft.monetary_amount == Decimal("45000.00")
    assert draft.monetary_currency == "GBP"


def test_plain_and_spaced_amounts_parse() -> None:
    assert _extracted(build_verbatim(body="a fee of £ 800")).monetary_amount == Decimal("800.00")


def test_no_amount_leaves_fields_unset() -> None:
    draft = _extracted(build_verbatim(body="No money is mentioned here."))
    assert draft.monetary_amount is None
    assert draft.monetary_currency is None


def test_absurd_amounts_are_treated_as_parse_artefacts() -> None:
    draft = _extracted(build_verbatim(body="reference £99999999999999 but a real £2,000 loss"))
    assert draft.monetary_amount == Decimal("2000.00")


def test_aggregates_are_skipped() -> None:
    draft = _extracted(build_aggregate(body="Firm received 42 complaints worth £1,000,000."))
    assert draft.monetary_amount is None
