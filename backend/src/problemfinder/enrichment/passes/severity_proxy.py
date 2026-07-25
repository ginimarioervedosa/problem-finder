"""A 0-to-1 severity proxy whose arithmetic is spelled out in its basis.

Runs last in the sequence: it reads what the monetary and resolution passes
left on the draft. Aggregates score their upheld share directly. Verbatims
stack a base with upheld outcome, monetary magnitude and hardship language;
severity_basis records exactly which parts fired, so no score is a black box.
"""

from decimal import Decimal

from problemfinder.domain.enrichment import ResolutionStatus
from problemfinder.domain.signal import AggregateSignal, ProblemSignal
from problemfinder.enrichment.protocol import EnrichmentDraft

_HARDSHIP_MARKERS = (
    "life savings",
    "financial hardship",
    "vulnerable",
    "vulnerability",
    "considerable distress",
    "significant distress",
    "borrowed money to",
    "lost everything",
)

_MONETARY_BANDS = (  # (floor, contribution, label) — first floor the amount clears wins
    (Decimal(100_000), 0.3, "amount ≥ £100k +0.3"),
    (Decimal(10_000), 0.2, "amount ≥ £10k +0.2"),
    (Decimal(1_000), 0.1, "amount ≥ £1k +0.1"),
)


class SeverityProxyPass:
    name = "severity_proxy"

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        if isinstance(signal, AggregateSignal):
            if signal.upheld_share is not None:
                draft.severity = round(signal.upheld_share, 4)
                draft.severity_basis = "aggregate upheld share"
            return
        score, parts = 0.2, ["base 0.2"]
        if draft.resolution is ResolutionStatus.UPHELD:
            score += 0.3
            parts.append("upheld +0.3")
        if draft.monetary_amount is not None:
            for floor, contribution, label in _MONETARY_BANDS:
                if draft.monetary_amount >= floor:
                    score += contribution
                    parts.append(label)
                    break
        text = f"{signal.title or ''} {signal.body}".casefold()
        if any(marker in text for marker in _HARDSHIP_MARKERS):
            score += 0.2
            parts.append("hardship language +0.2")
        draft.severity = min(round(score, 2), 1.0)
        draft.severity_basis = ", ".join(parts)
