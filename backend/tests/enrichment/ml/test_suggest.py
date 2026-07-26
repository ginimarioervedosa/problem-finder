"""End to end over a stub encoder: verbatims in, proposed clusters out.

Needs scikit-learn and numpy, so the zero-ML CI environment skips this file
visibly; that skip is the extras boundary working as designed.
"""

from collections.abc import Generator, Sequence
from pathlib import Path

import pytest
from sqlalchemy import Engine

pytest.importorskip("numpy", reason="ml extras not installed (zero-ML environment)")
pytest.importorskip("sklearn", reason="ml extras not installed (zero-ML environment)")

import numpy as np

from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.enrichment.ml import review
from problemfinder.enrichment.ml.suggest import propose_themes
from problemfinder.persistence.engine import session_scope
from problemfinder.settings import get_settings
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


class TwoTopicEncoder:
    """Scam texts on one axis, delay texts on another; no model needed."""

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return np.array(
            [
                [1.0, 0.001 * index, 0.0] if "scam" in text else [0.0, 1.0, 0.001 * index]
                for index, text in enumerate(texts)
            ]
        )


@pytest.fixture
def seeded_corpus(
    pipeline_db: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None]:
    monkeypatch.setenv("PF_ML_CACHE_DIR", str(tmp_path / "ml"))
    get_settings.cache_clear()
    scams = [
        build_verbatim(external_id=f"scam-{i}", body=f"A cryptocurrency scam case number {i}.")
        for i in range(4)
    ]
    delays = [
        build_verbatim(external_id=f"delay-{i}", body=f"A pension transfer delay case {i}.")
        for i in range(4)
    ]
    with session_scope() as session:
        seed_signals(session, [*scams, *delays, build_aggregate()])
    yield
    get_settings.cache_clear()


def test_verbatims_cluster_into_proposed_suggestions(seeded_corpus: None) -> None:
    report = propose_themes(min_cluster_size=3, encoder=TwoTopicEncoder())
    assert report.verbatims == 8  # the aggregate sat it out
    assert report.clusters == 2
    proposed = review.list_reviews(SuggestionStatus.PROPOSED)
    assert len(proposed) == 2
    assert all(s.method == "hdbscan:v1" and s.size == 4 for s in proposed)
    scam_cluster = next(s for s in proposed if "scam" in s.top_terms)
    assert scam_cluster.suggested_theme == "fraud_and_scams"
    assert len(scam_cluster.member_signal_ids) == 4
    assert set(scam_cluster.representative_signal_ids) <= set(scam_cluster.member_signal_ids)


def test_rerun_replaces_proposals_but_keeps_decisions(seeded_corpus: None) -> None:
    propose_themes(min_cluster_size=3, encoder=TwoTopicEncoder())
    accepted = review.accept(0)
    report = propose_themes(min_cluster_size=3, encoder=TwoTopicEncoder())
    assert report.replaced == 1  # only the undecided proposal was swapped out
    statuses = [s.status for s in review.list_reviews()]
    assert statuses.count(SuggestionStatus.ACCEPTED) == 1
    assert statuses.count(SuggestionStatus.PROPOSED) == 2
    assert review.list_reviews(SuggestionStatus.ACCEPTED)[0].id == accepted.id
