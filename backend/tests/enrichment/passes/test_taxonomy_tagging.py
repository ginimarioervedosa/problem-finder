"""Theme scoring, sub-theme selection and category -> domain mapping."""

from problemfinder.domain.dimensions import ProductDomain
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.passes.taxonomy_tagging import TaxonomyTaggingPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from problemfinder.enrichment.taxonomy import SubTheme, Taxonomy, Theme
from tests.support.builders import build_aggregate, build_verbatim

TAXONOMY = Taxonomy(
    product_domains={"Banking & Credit": ProductDomain.BANKING_AND_CREDIT},
    themes=(
        Theme(
            name="fraud_and_scams",
            keywords=("scam", "fraudster"),
            sub_themes=(SubTheme(name="investment_scam", keywords=("investment scam",)),),
        ),
        Theme(name="delays_and_service_failures", keywords=("unreasonable delay",)),
    ),
)


def _tagged(signal: ProblemSignal) -> EnrichmentDraft:
    draft = EnrichmentDraft()
    TaxonomyTaggingPass(TAXONOMY).apply(signal, draft)
    return draft


def test_most_distinct_keyword_hits_wins() -> None:
    signal = build_verbatim(
        body="A fraudster ran an investment scam despite the unreasonable delay."
    )
    draft = _tagged(signal)
    assert draft.theme == "fraud_and_scams"  # two hits beat one
    assert draft.sub_theme == "investment_scam"


def test_no_matching_keywords_leaves_theme_unset() -> None:
    draft = _tagged(build_verbatim(body="A perfectly ordinary account statement."))
    assert draft.theme is None
    assert draft.sub_theme is None


def test_matching_is_case_insensitive() -> None:
    assert _tagged(build_verbatim(body="THIS WAS A SCAM.")).theme == "fraud_and_scams"


def test_aggregate_gets_domain_from_category_but_no_theme() -> None:
    draft = _tagged(build_aggregate())  # builder category: Banking & Credit
    assert draft.product_domain is ProductDomain.BANKING_AND_CREDIT
    assert draft.theme is None


def test_unmapped_category_leaves_domain_unset() -> None:
    draft = _tagged(build_aggregate(category="Never Heard Of It"))
    assert draft.product_domain is None
