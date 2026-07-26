"""The review step: accept maps a cluster onto a theme, reject retires it."""

import pytest
from sqlalchemy import Engine

from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.enrichment.ml import review
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import theme_suggestions
from tests.support.builders import build_suggestion

pytestmark = pytest.mark.db


@pytest.fixture
def proposals(pipeline_db: Engine) -> None:
    with session_scope() as session:
        theme_suggestions.replace_proposed(
            session,
            "hdbscan:v1",
            [
                build_suggestion(cluster_key=0, suggested_theme="fraud_and_scams"),
                build_suggestion(cluster_key=1, suggested_theme=None, label="crypto_wallet_loss"),
            ],
        )


def test_accept_maps_onto_the_named_theme(proposals: None) -> None:
    decided = review.accept(0, "charges_and_fees")
    assert decided.status is SuggestionStatus.ACCEPTED
    assert decided.mapped_theme == "charges_and_fees"
    assert decided.decided_at is not None


def test_accept_defaults_to_the_suggested_theme(proposals: None) -> None:
    assert review.accept(0).mapped_theme == "fraud_and_scams"


def test_accept_falls_back_to_the_label_for_new_territory(proposals: None) -> None:
    assert review.accept(1).mapped_theme == "crypto_wallet_loss"


def test_reject_retires_the_cluster(proposals: None) -> None:
    decided = review.reject(1)
    assert decided.status is SuggestionStatus.REJECTED
    assert decided.mapped_theme is None
    assert review.list_reviews(SuggestionStatus.PROPOSED)[0].cluster_key == 0


def test_unknown_cluster_key_raises_with_the_remedy(proposals: None) -> None:
    with pytest.raises(review.UnknownClusterError, match="pf ml suggestions"):
        review.accept(99)


def test_decided_clusters_cannot_be_decided_twice(proposals: None) -> None:
    review.accept(0)
    with pytest.raises(review.UnknownClusterError):
        review.reject(0)
