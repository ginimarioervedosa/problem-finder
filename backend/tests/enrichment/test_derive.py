"""The full rules:v1 fold over one signal produces a coherent enrichment."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from problemfinder.domain.dimensions import ProductDomain, WealthSegment
from problemfinder.domain.enrichment import ResolutionStatus
from problemfinder.enrichment.derive import derive_enrichment
from problemfinder.enrichment.ruleset import RULES_METHOD, rules_v1
from problemfinder.enrichment.taxonomy import SubTheme, Taxonomy, Theme
from tests.support.builders import build_verbatim

TAXONOMY = Taxonomy(
    product_domains={"Banking and Payments": ProductDomain.BANKING_AND_CREDIT},
    themes=(
        Theme(
            name="fraud_and_scams",
            keywords=("scam",),
            sub_themes=(SubTheme(name="investment_scam", keywords=("investment scam",)),),
        ),
    ),
)
COMPUTED_AT = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def test_passes_compose_into_one_enrichment() -> None:
    signal = build_verbatim(
        category="Banking and Payments",
        body=(
            "Mr B fell for an investment scam and transferred £45,000 from his pension "
            "drawdown, causing significant distress."
        ),
        extras={"outcome": "Upheld"},
    )
    enrichment = derive_enrichment(
        signal, rules_v1(TAXONOMY), version=1, method=RULES_METHOD, computed_at=COMPUTED_AT
    )
    assert enrichment.signal_id == signal.id
    assert enrichment.version == 1
    assert enrichment.method == "rules:v1"
    assert enrichment.computed_at == COMPUTED_AT
    assert enrichment.theme == "fraud_and_scams"
    assert enrichment.sub_theme == "investment_scam"
    assert enrichment.product_domain is ProductDomain.BANKING_AND_CREDIT
    assert enrichment.monetary_amount == Decimal("45000.00")
    assert enrichment.monetary_currency == "GBP"
    assert enrichment.resolution is ResolutionStatus.UPHELD
    assert enrichment.segment is WealthSegment.RETIREE
    assert enrichment.severity == pytest.approx(0.9)
    assert enrichment.severity_basis is not None and "upheld +0.3" in enrichment.severity_basis
