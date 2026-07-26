"""Propose candidate themes: embed the verbatims, cluster, describe, store.

Aggregate signals sit this out (their bodies are formulaic); every stored
verbatim is embedded and clustered, dense clusters become ThemeSuggestion
rows, and HDBSCAN's noise stays unproposed. Rerunning replaces the still
undecided proposals for this method, so reclustering is always safe.
"""

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.theme_suggestion import ThemeSuggestion
from problemfinder.enrichment.ml.cluster import cluster_embeddings, representative_indices
from problemfinder.enrichment.ml.embeddings import Encoder, embed_texts
from problemfinder.enrichment.ml.match import closest_theme
from problemfinder.enrichment.ml.terms import distinctive_terms, label_from_terms
from problemfinder.enrichment.taxonomy import Taxonomy, load_taxonomy
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import signals, theme_suggestions
from problemfinder.settings import get_settings

ML_METHOD = "hdbscan:v1"


class SuggestReport(BaseModel):
    """What one `pf ml cluster` run found, for the CLI to narrate."""

    verbatims: int
    clusters: int
    noise: int
    replaced: int


def propose_themes(*, min_cluster_size: int = 15, encoder: Encoder | None = None) -> SuggestReport:
    """Cluster every stored verbatim into fresh proposed theme suggestions."""
    settings = get_settings()
    taxonomy = load_taxonomy(settings.taxonomy_path)
    created_at = datetime.now(tz=UTC)
    with session_scope() as session:
        verbatims = [
            signal
            for chunk in signals.stream_all(session)
            for signal in chunk
            if isinstance(signal, VerbatimSignal)
        ]
        matrix = embed_texts([signal.body for signal in verbatims], settings.ml_cache_dir, encoder)
        labels = cluster_embeddings(matrix, min_cluster_size=min_cluster_size)
        representatives = representative_indices(matrix, labels)
        suggestions = _build_suggestions(verbatims, labels, representatives, taxonomy, created_at)
        replaced, _ = theme_suggestions.replace_proposed(session, ML_METHOD, suggestions)
    return SuggestReport(
        verbatims=len(verbatims),
        clusters=len(suggestions),
        noise=labels.count(-1),
        replaced=replaced,
    )


def _build_suggestions(
    verbatims: list[VerbatimSignal],
    labels: list[int],
    representatives: dict[int, list[int]],
    taxonomy: Taxonomy,
    created_at: datetime,
) -> list[ThemeSuggestion]:
    members: dict[int, list[VerbatimSignal]] = {}
    for signal, label in zip(verbatims, labels, strict=True):
        if label != -1:
            members.setdefault(label, []).append(signal)
    terms = distinctive_terms({key: [s.body for s in group] for key, group in members.items()})
    return [
        ThemeSuggestion(
            id=uuid4(),
            method=ML_METHOD,
            cluster_key=key,
            label=label_from_terms(terms[key]),
            top_terms=terms[key],
            size=len(group),
            member_signal_ids=tuple(signal.id for signal in group),
            representative_signal_ids=tuple(verbatims[i].id for i in representatives[key]),
            suggested_theme=closest_theme(terms[key], taxonomy),
            created_at=created_at,
        )
        for key, group in sorted(members.items(), key=lambda item: -len(item[1]))
    ]
