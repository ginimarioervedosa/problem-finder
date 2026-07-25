"""What an enrichment pass is: one deterministic rule set over one signal.

Passes never see storage; each reads a signal and fills the attributes it
owns on a shared mutable draft. The runner folds a fixed pass sequence over
the draft and freezes the result into a `SignalEnrichment`.
"""

from typing import Protocol, runtime_checkable

from problemfinder.domain.enrichment import DerivedAttributes
from problemfinder.domain.signal import ProblemSignal


class EnrichmentDraft(DerivedAttributes):
    """Mutable working copy of the derived attributes, filled pass by pass."""


@runtime_checkable
class EnrichmentPass(Protocol):
    """One rule set. Pure over domain models: no I/O, no storage, no clock."""

    name: str

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        """Read the signal (and earlier passes' draft fields), write your own."""
        ...
