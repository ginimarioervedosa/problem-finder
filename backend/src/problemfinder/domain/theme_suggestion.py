"""A candidate theme proposed by clustering, awaiting a review decision.

Clustering proposes; a person disposes. Each suggestion is one cluster of
verbatim signals with the distinctive terms that describe it and, where the
existing taxonomy already covers it, the closest matching theme. Accepting a
suggestion maps its members onto a theme name; the enrichment runner then
carries that mapping into versioned enrichment rows. Suggestions are derived
and disposable: reclustering replaces undecided rows wholesale.
"""

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class SuggestionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class MlThemeAssignment(BaseModel):
    """What accepting a suggestion means for one member signal."""

    model_config = ConfigDict(frozen=True)

    theme: str
    method: str


class ThemeSuggestion(BaseModel):
    """One proposed cluster: its members, its evidence, and its review state."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    method: str
    cluster_key: int
    label: str
    top_terms: tuple[str, ...] = Field(min_length=1)
    size: int = Field(ge=1)
    member_signal_ids: tuple[UUID, ...] = Field(min_length=1)
    representative_signal_ids: tuple[UUID, ...] = Field(min_length=1)
    suggested_theme: str | None = None
    status: SuggestionStatus = SuggestionStatus.PROPOSED
    mapped_theme: str | None = None
    created_at: AwareDatetime
    decided_at: AwareDatetime | None = None
