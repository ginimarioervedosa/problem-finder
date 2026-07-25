"""Resolution from the source's own outcome field, never inferred from prose.

Verbatim sources that publish an outcome (fos_decisions stores it in
extras["outcome"]) map onto the shared enum; an outcome we cannot map is
UNKNOWN, and no outcome at all stays None. Aggregates stay None: their
outcome is already the upheld_share on the signal itself.
"""

from problemfinder.domain.enrichment import ResolutionStatus
from problemfinder.domain.signal import ProblemSignal, VerbatimSignal
from problemfinder.enrichment.protocol import EnrichmentDraft

_OUTCOMES = {
    "upheld": ResolutionStatus.UPHELD,
    "not upheld": ResolutionStatus.NOT_UPHELD,
    "settled": ResolutionStatus.SETTLED,
    "proactively settled": ResolutionStatus.PROACTIVELY_SETTLED,
}


class ResolutionStatusPass:
    name = "resolution_status"

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        if not isinstance(signal, VerbatimSignal):
            return
        outcome = signal.extras.get("outcome")
        if isinstance(outcome, str) and outcome.strip():
            draft.resolution = _OUTCOMES.get(outcome.strip().casefold(), ResolutionStatus.UNKNOWN)
