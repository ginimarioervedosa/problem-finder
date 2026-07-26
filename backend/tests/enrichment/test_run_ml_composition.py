"""Accepted cluster mappings flow into enrichment rows with honest methods."""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import Engine

from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.enrichment.run import run_enrichment
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import signal_enrichments, theme_suggestions
from problemfinder.settings import get_settings
from tests.support.builders import build_suggestion, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db

TAXONOMY = """
product_domains: {}
themes:
  - name: fraud_and_scams
    keywords: [scam]
"""


@pytest.fixture
def corpus(
    pipeline_db: Engine, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[VerbatimSignal, VerbatimSignal]]:
    taxonomy_path = tmp_path / "taxonomy.yaml"
    taxonomy_path.write_text(TAXONOMY)
    monkeypatch.setenv("PF_TAXONOMY_PATH", str(taxonomy_path))
    get_settings.cache_clear()
    ruled = build_verbatim(external_id="ruled", body="An investment scam took everything.")
    unruled = build_verbatim(external_id="unruled", body="The pension transfer took a year.")
    with session_scope() as session:
        seed_signals(session, [ruled, unruled])
    yield ruled, unruled
    get_settings.cache_clear()


def accept_cluster_over(*signals: VerbatimSignal, theme: str) -> None:
    suggestion = build_suggestion(member_signal_ids=tuple(s.id for s in signals))
    with session_scope() as session:
        theme_suggestions.replace_proposed(session, suggestion.method, [suggestion])
        theme_suggestions.decide(
            session, suggestion.id, SuggestionStatus.ACCEPTED, theme, datetime.now(tz=UTC)
        )


def latest_by_external_id(*signals: VerbatimSignal) -> dict[str, tuple[str | None, str]]:
    with session_scope() as session:
        latest = signal_enrichments.latest_for(session, [s.id for s in signals])
    return {s.external_id: (latest[s.id].theme, latest[s.id].method) for s in signals}


def test_accepted_mappings_fill_gaps_and_compose_the_method(
    corpus: tuple[VerbatimSignal, VerbatimSignal],
) -> None:
    ruled, unruled = corpus
    accept_cluster_over(ruled, unruled, theme="transfer_delays")

    first = run_enrichment()
    assert first.written == 2
    rows = latest_by_external_id(ruled, unruled)
    assert rows["ruled"] == ("fraud_and_scams", "rules:v1")  # rules keep authority
    assert rows["unruled"] == ("transfer_delays", "rules:v1+hdbscan:v1")

    second = run_enrichment(recompute=True)
    assert (second.written, second.unchanged) == (0, 2)


def test_a_new_acceptance_rewrites_only_the_signals_it_themes(
    corpus: tuple[VerbatimSignal, VerbatimSignal],
) -> None:
    ruled, unruled = corpus
    run_enrichment()
    accept_cluster_over(ruled, unruled, theme="transfer_delays")

    report = run_enrichment(recompute=True)
    assert (report.written, report.unchanged) == (1, 1)  # the ruled signal never changed
    theme, method = latest_by_external_id(unruled)["unruled"]
    assert (theme, method) == ("transfer_delays", "rules:v1+hdbscan:v1")
