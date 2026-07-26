"""Cluster terms map onto the closest existing theme, or honestly onto none."""

from problemfinder.enrichment.ml.match import closest_theme
from problemfinder.enrichment.taxonomy import Taxonomy

TAXONOMY = Taxonomy.model_validate(
    {
        "product_domains": {},
        "themes": [
            {"name": "fraud_and_scams", "keywords": ["scam", "fraudster", "safe account"]},
            {"name": "delays", "keywords": ["delay", "unreasonable delay"]},
            {"name": "scam_recovery", "keywords": ["scam", "recovery"]},
        ],
    }
)


def test_most_keyword_hits_wins() -> None:
    assert closest_theme(["scam", "fraudster", "crypto"], TAXONOMY) == "fraud_and_scams"


def test_single_word_terms_hit_multi_word_keywords() -> None:
    assert closest_theme(["delay"], TAXONOMY) == "delays"


def test_ties_go_to_declaration_order() -> None:
    # "scam" alone hits fraud_and_scams and scam_recovery equally; first declared wins.
    assert closest_theme(["scam"], TAXONOMY) == "fraud_and_scams"


def test_no_overlap_returns_none() -> None:
    assert closest_theme(["mortgage", "valuation"], TAXONOMY) is None
