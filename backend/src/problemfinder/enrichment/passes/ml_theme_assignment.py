"""Accepted cluster mappings, folded in as one more enrichment pass.

The pass runs after the rules and fills the theme only where they left
none: reviewed keyword rules stay authoritative, clustering extends their
reach. It is pure over domain models; the assignments arrive as data (built
from accepted theme suggestions), never from storage or an ML library, so
enrichment with ML-derived themes runs fine on a zero-ML install.
"""

from collections.abc import Mapping
from uuid import UUID

from problemfinder.domain.signal import ProblemSignal
from problemfinder.domain.theme_suggestion import MlThemeAssignment
from problemfinder.enrichment.protocol import EnrichmentDraft


class MlThemeAssignmentPass:
    """Fill unthemed signals from accepted cluster mappings, recording which."""

    name = "ml_theme_assignment"

    def __init__(self, assignments: Mapping[UUID, MlThemeAssignment]) -> None:
        self._assignments = assignments
        self._applied: set[UUID] = set()

    def apply(self, signal: ProblemSignal, draft: EnrichmentDraft) -> None:
        assignment = self._assignments.get(signal.id)
        if assignment is None or draft.theme is not None:
            return
        draft.theme = assignment.theme
        self._applied.add(signal.id)

    def applied_method(self, signal_id: UUID) -> str | None:
        """The ML method that themed this signal, or None if the rules did."""
        if signal_id not in self._applied:
            return None
        return self._assignments[signal_id].method
