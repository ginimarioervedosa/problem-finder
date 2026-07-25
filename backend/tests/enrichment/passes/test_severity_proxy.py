"""Severity stacks named contributions and spells them out in its basis."""

from decimal import Decimal

import pytest

from problemfinder.domain.enrichment import ResolutionStatus
from problemfinder.enrichment.passes.severity_proxy import SeverityProxyPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_aggregate, build_verbatim


def test_aggregate_scores_its_upheld_share() -> None:
    draft = EnrichmentDraft()
    SeverityProxyPass().apply(build_aggregate(upheld_share=0.25), draft)
    assert draft.severity == pytest.approx(0.25)
    assert draft.severity_basis == "aggregate upheld share"


def test_aggregate_without_upheld_share_stays_unscored() -> None:
    draft = EnrichmentDraft()
    SeverityProxyPass().apply(build_aggregate(upheld_share=None), draft)
    assert draft.severity is None


def test_verbatim_base_score_alone() -> None:
    draft = EnrichmentDraft()
    SeverityProxyPass().apply(build_verbatim(body="A minor mix-up."), draft)
    assert draft.severity == pytest.approx(0.2)
    assert draft.severity_basis == "base 0.2"


def test_contributions_stack_and_the_basis_names_each() -> None:
    draft = EnrichmentDraft(resolution=ResolutionStatus.UPHELD, monetary_amount=Decimal("45000.00"))
    signal = build_verbatim(body="She lost her life savings.")
    SeverityProxyPass().apply(signal, draft)
    assert draft.severity == pytest.approx(0.9)  # 0.2 base + 0.3 upheld + 0.2 £10k + 0.2 hardship
    assert draft.severity_basis == (
        "base 0.2, upheld +0.3, amount ≥ £10k +0.2, hardship language +0.2"
    )


def test_score_is_capped_at_one() -> None:
    draft = EnrichmentDraft(
        resolution=ResolutionStatus.UPHELD, monetary_amount=Decimal("250000.00")
    )
    SeverityProxyPass().apply(build_verbatim(body="Their life savings, gone."), draft)
    assert draft.severity == 1.0
