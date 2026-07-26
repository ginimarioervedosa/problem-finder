"""One command rebuilds every derived attribute from the stored signals.

Signals stream through the rules:v1 sequence, extended by the ML assignment
pass whenever accepted theme suggestions exist; a new (signal_id, version)
row is appended only where the derived attributes actually changed, so
`pf enrich run --recompute` is idempotent: a second identical run writes
nothing. Without --recompute, only signals with no enrichment are computed.
Each row's method records what produced it: `rules:v1` alone, or
`rules:v1+hdbscan:v1` where an accepted cluster themed the signal.
"""

from datetime import UTC, datetime

from pydantic import BaseModel

from problemfinder.domain.enrichment import SignalEnrichment
from problemfinder.domain.signal import ProblemSignal
from problemfinder.enrichment.derive import derive_enrichment
from problemfinder.enrichment.passes.ml_theme_assignment import MlThemeAssignmentPass
from problemfinder.enrichment.protocol import EnrichmentPass
from problemfinder.enrichment.ruleset import RULES_METHOD, rules_v1
from problemfinder.enrichment.taxonomy import load_taxonomy
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import signal_enrichments, signals, theme_suggestions
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
    rules = rules_v1(load_taxonomy(get_settings().taxonomy_path))
    computed_at = datetime.now(tz=UTC)
    report = EnrichmentRunReport()
    with session_scope() as session:
        ml_pass = MlThemeAssignmentPass(theme_suggestions.accepted_assignments(session))
        passes: tuple[EnrichmentPass, ...] = (*rules, ml_pass)
        for chunk in signals.stream_all(session):
            latest = signal_enrichments.latest_for(session, [signal.id for signal in chunk])
            fresh = [
                enrichment
                for signal in chunk
                if (
                    enrichment := _derive_if_due(
                        signal,
                        latest.get(signal.id),
                        passes,
                        ml_pass,
                        computed_at,
                        report,
                        recompute,
                    )
                )
            ]
            report.written += signal_enrichments.append_many(session, fresh)
    return report


def _derive_if_due(  # noqa: PLR0913, PLR0917 -- the fold's full context, by design
    signal: ProblemSignal,
    current: SignalEnrichment | None,
    passes: tuple[EnrichmentPass, ...],
    ml_pass: MlThemeAssignmentPass,
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
    if ml_method := ml_pass.applied_method(signal.id):
        fresh = fresh.model_copy(update={"method": f"{RULES_METHOD}+{ml_method}"})
    if current is not None and _same_attributes(fresh, current):
        report.unchanged += 1
        return None
    return fresh


def _same_attributes(fresh: SignalEnrichment, latest: SignalEnrichment) -> bool:
    return fresh.model_dump(exclude=_NOT_COMPARED) == latest.model_dump(exclude=_NOT_COMPARED)
