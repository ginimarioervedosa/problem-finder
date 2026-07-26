"""The ML assignment pass: fills gaps, defers to rules, remembers its work."""

from uuid import uuid4

from problemfinder.domain.theme_suggestion import MlThemeAssignment
from problemfinder.enrichment.passes.ml_theme_assignment import MlThemeAssignmentPass
from problemfinder.enrichment.protocol import EnrichmentDraft
from tests.support.builders import build_verbatim

ASSIGNMENT = MlThemeAssignment(theme="crypto_wallet_loss", method="hdbscan:v1")


def test_fills_the_theme_the_rules_left_empty() -> None:
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({signal.id: ASSIGNMENT})
    draft = EnrichmentDraft()
    ml_pass.apply(signal, draft)
    assert draft.theme == "crypto_wallet_loss"
    assert ml_pass.applied_method(signal.id) == "hdbscan:v1"


def test_never_overrides_a_rules_theme() -> None:
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({signal.id: ASSIGNMENT})
    draft = EnrichmentDraft(theme="fraud_and_scams")
    ml_pass.apply(signal, draft)
    assert draft.theme == "fraud_and_scams"
    assert ml_pass.applied_method(signal.id) is None


def test_unassigned_signals_pass_through_untouched() -> None:
    signal = build_verbatim()
    ml_pass = MlThemeAssignmentPass({uuid4(): ASSIGNMENT})
    draft = EnrichmentDraft()
    ml_pass.apply(signal, draft)
    assert draft.theme is None
    assert ml_pass.applied_method(signal.id) is None
