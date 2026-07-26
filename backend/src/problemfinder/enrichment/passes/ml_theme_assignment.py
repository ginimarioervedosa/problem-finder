"""Accepted cluster mappings, folded in as one more enrichment pass.

The pass runs after the rules and sets its members' theme outright: an
accepted mapping is a human-reviewed decision about what those signals are
about, which outranks a keyword coincidence (long decision texts trip
generic keywords constantly — the first live cluster, dental aligners, was
100% rule-tagged as payment disputes). Rules keep every other attribute,
and every signal outside an accepted cluster. The pass is pure over domain
models; assignments arrive as data built from accepted theme suggestions,
never from storage or an ML library, so enrichment with ML-derived themes
runs fine on a zero-ML install.
"""

from collections.abc import Mapping
from uuid import UUID

from problemfinder.domain.signal import ProblemSignal
from problemfinder.domain.theme_suggestion import MlThemeAssignment
from problemfinder.enrichment.protocol import EnrichmentDraft


class MlThemeAssignmentPass:
    """Carry accepted cluster mappings onto their members, recording which."""

    name = "ml_theme_assignment"

    def __init__(self, assignments: Mapping[UUID, MlThemeAssignment]) -> None:
        self._assignments = assignments
        self._applied: set[UUID] = set()

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        assignment = self._assignments.get(signal.id)
        if assignment is None:
            return
        if draft.theme != assignment.theme:
            draft.sub_theme = None  # a sub-theme of a replaced theme cannot survive it
        draft.theme = assignment.theme
        self._applied.add(signal.id)

    def applied_method(self, signal_id: UUID) -> str | None:
        """The ML method that themed this signal, or None if the rules did."""
        if signal_id not in self._applied:
            return None
        return self._assignments[signal_id].method
