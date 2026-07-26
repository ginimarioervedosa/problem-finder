"""Distinctive terms: cluster-specific words rise, shared boilerplate sinks."""

from problemfinder.enrichment.ml.terms import distinctive_terms, label_from_terms

SCAM_DOCS = [
    "The complaint concerns a cryptocurrency scam and a fraudster.",
    "The complaint concerns another scam; the fraudster vanished.",
]
DELAY_DOCS = [
    "The complaint concerns a pension transfer delay.",
    "The complaint concerns a delay in the pension transfer paperwork.",
]


def test_each_cluster_leads_with_its_own_vocabulary() -> None:
    terms = distinctive_terms({0: SCAM_DOCS, 1: DELAY_DOCS}, top=3)
    assert "scam" in terms[0]
    assert "delay" in terms[1]
    assert "scam" not in terms[1]


def test_shared_boilerplate_scores_below_distinctive_terms() -> None:
    terms = distinctive_terms({0: SCAM_DOCS, 1: DELAY_DOCS}, top=3)
    for key in (0, 1):
        assert "complaint" not in terms[key]
        assert "concerns" not in terms[key]


def test_stopwords_never_appear() -> None:
    terms = distinctive_terms({0: ["the and that with was", "another and the with"]}, top=5)
    assert "the" not in terms[0]
    assert "and" not in terms[0]


def test_label_joins_the_leading_terms() -> None:
    assert label_from_terms(("scam", "fraudster", "crypto", "extra")) == "scam_fraudster_crypto"
