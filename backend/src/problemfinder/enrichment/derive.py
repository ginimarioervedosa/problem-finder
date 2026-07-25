"""Fold the pass sequence over one signal. Pure: no storage, no clock."""

from collections.abc import Sequence
from datetime import datetime

from problemfinder.domain.enrichment import SignalEnrichment
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.protocol import EnrichmentDraft, EnrichmentPass


def derive_enrichment(
    signal: ProblemSignal,
    passes: Sequence[EnrichmentPass],
    *,
    version: int,
    method: str,
    computed_at: datetime,
) -> SignalEnrichment:
    draft = EnrichmentDraft()
    for enrichment_pass in passes:
        enrichment_pass.apply(signal, draft)
    return SignalEnrichment(
        signal_id=signal.id,
        version=version,
        method=method,
        computed_at=computed_at,
        **draft.model_dump(),
    )
