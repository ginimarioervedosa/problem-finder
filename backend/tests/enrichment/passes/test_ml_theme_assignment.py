"""The ML assignment pass: accepted review decisions own their members' theme."""

from uuid import uuid4

from problemfinder.domain.theme_suggestion import MlThemeAssignment
from problemfinder.enrichment.passes.ml_theme_assignment import MlThemeAssignmentPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_verbatim

ASSIGNMENT = MlThemeAssignment(theme="dental_aligner_aftercare", method="hdbscan:v1")


def test_fills_the_theme_the_rules_left_empty() -> None:
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({signal.id: ASSIGNMENT})
    draft = EnrichmentDraft()
    ml_pass.apply(signal, draft)
    assert draft.theme == "dental_aligner_aftercare"
    assert ml_pass.applied_method(signal.id) == "hdbscan:v1"


def test_overrides_a_keyword_theme_because_the_mapping_was_reviewed() -> None:
    # Real case: dental-aligner decisions rule-tagged disputed_transactions via
    # incidental chargeback wording; the accepted cluster is the truer theme.
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({signal.id: ASSIGNMENT})
    draft = EnrichmentDraft(theme="disputed_transactions", sub_theme="chargeback")
    ml_pass.apply(signal, draft)
    assert draft.theme == "dental_aligner_aftercare"
    assert draft.sub_theme is None  # the old theme's sub-theme cannot survive it
    assert ml_pass.applied_method(signal.id) == "hdbscan:v1"


def test_an_agreeing_mapping_keeps_the_sub_theme() -> None:
    signal = build_verbatim()
    agreeing = MlThemeAssignment(theme="fraud_and_scams", method="hdbscan:v1")
    ml_pass = MlThemeAssignmentPass({signal.id: agreeing})
    draft = EnrichmentDraft(theme="fraud_and_scams", sub_theme="investment_scam")
    ml_pass.apply(signal, draft)
    assert draft.sub_theme == "investment_scam"
    assert ml_pass.applied_method(signal.id) == "hdbscan:v1"


def test_unassigned_signals_pass_through_untouched() -> None:
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({uuid4(): ASSIGNMENT})
    draft = EnrichmentDraft(theme="fraud_and_scams")
    ml_pass.apply(signal, draft)
    assert draft.theme == "fraud_and_scams"
    assert ml_pass.applied_method(signal.id) is None
