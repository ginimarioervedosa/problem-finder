"""One command rebuilds every derived attribute from the stored signals.

Signals stream through the rules:v1 sequence; a new (signal_id, version) row
is appended only where the derived attributes actually changed, so
`pf enrich run --recompute` is idempotent: a second identical run writes
nothing. Without --recompute, only signals with no enrichment are computed.
"""

from datetime import UTC, datetime

from pydantic import BaseModel

from problemfinder.domain.enrichment import SignalEnrichment
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.derive import derive_enrichment
from problemfinder.enrichment.protocol import EnrichmentPass
from problemfinder.enrichment.ruleset import RULES_METHOD, rules_v1
from problemfinder.enrichment.taxonomy import load_taxonomy
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import signal_enrichments, signals
from problemfinder.settings import get_settings

_NOT_COMPARED = {"version", "computed_at"}  # method IS compared: a ruleset bump is a change


class EnrichmentRunReport(BaseModel):
    """What one `pf enrich run` did, for the CLI to narrate."""

    processed: int = 0
    written: int = 0
    unchanged: int = 0
    skipped: int = 0


def run_enrichment(*, recompute: bool = False) -> EnrichmentRunReport:
    """Enrich stored signals; with recompute, re-derive even the already enriched."""
    passes = rules_v1(load_taxonomy(get_settings().taxonomy_path))
    computed_at = datetime.now(tz=UTC)
    report = EnrichmentRunReport()
    with session_scope() as session:
        for chunk in signals.stream_all(session):
            latest = signal_enrichments.latest_for(session, [signal.id for signal in chunk])
            fresh = [
                enrichment
                for signal in chunk
                if (
                    enrichment := _derive_if_due(
                        signal, latest.get(signal.id), passes, computed_at, report, recompute
                    )
                )
            ]
            report.written += signal_enrichments.append_many(session, fresh)
    return report


def _derive_if_due(  # noqa: PLR0913, PLR0917 -- the fold's full context, by design
    signal: ProblemSignal,
    current: SignalEnrichment | None,
    passes: tuple[EnrichmentPass, ...],
    computed_at: datetime,
    report: EnrichmentRunReport,
    recompute: bool,
) -> SignalEnrichment | None:
    """Derive one signal's enrichment; None when nothing needs writing."""
    if current is not None and not recompute:
        report.skipped += 1
        return None
    report.processed += 1
    fresh = derive_enrichment(
        signal,
        passes,
        version=current.version + 1 if current else 1,
        method=RULES_METHOD,
        computed_at=computed_at,
    )
    if current is not None and _same_attributes(fresh, current):
        report.unchanged += 1
        return None
    return fresh


def _same_attributes(fresh: SignalEnrichment, latest: SignalEnrichment) -> bool:
    return fresh.model_dump(exclude=_NOT_COMPARED) == latest.model_dump(exclude=_NOT_COMPARED)
