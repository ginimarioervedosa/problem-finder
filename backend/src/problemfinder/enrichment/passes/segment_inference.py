"""Wealth segment, inferred from how the complainant's money is described.

Rules fire in declared priority order and only on a verbatim's own words; a
signal with no clear marker stays None rather than guessing. This is a
deliberately coarse proxy for HNW-relevance until the ML passes of phase 5.
"""

from problemfinder.domain.dimensions import WealthSegment
from problemfinder.domain.signal import ProblemSignal, VerbatimSignal
from problemfinder.enrichment.protocol import EnrichmentDraft

_RULES: tuple[tuple[WealthSegment, tuple[str, ...]], ...] = (
    (
        WealthSegment.BUSINESS_OWNER,
        (
            "business account",
            "limited company",
            "sole trader",
            "his business",
            "her business",
            "their business",
            "the director",
            "company account",
        ),
    ),
    (
        WealthSegment.PROPERTY_INVESTOR,
        ("buy-to-let", "buy to let", "landlord", "rental property", "tenanted", "second property"),
    ),
    (
        WealthSegment.INHERITED_WEALTH,
        (
            "inheritance",
            "inherited",
            "estate of the late",
            "executor",
            "probate",
            "beneficiary of the estate",
        ),
    ),
    (
        WealthSegment.RETIREE,
        ("pension", "annuity", "retirement", "retired", "drawdown"),
    ),
)


class SegmentInferencePass:
    name = "segment_inference"

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        if not isinstance(signal, VerbatimSignal):
            return
        text = f"{signal.title or ''} {signal.body}".casefold()
        draft.segment = next(
            (segment for segment, markers in _RULES if any(marker in text for marker in markers)),
            None,
        )
