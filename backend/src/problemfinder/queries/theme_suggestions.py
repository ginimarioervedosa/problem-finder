"""Theme suggestions for the dashboard, with a taste of their evidence.

Each suggestion carries its representative verbatims (the members nearest
the cluster centroid) as title-and-snippet previews, so a review decision
can be made from the page rather than from raw ids. Member id lists stay
out of the payload: the UI ranks and reads, the CLI decides.
"""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from problemfinder.domain.theme_suggestion import SuggestionStatus, ThemeSuggestion
from problemfinder.persistence.orm import SignalRow
from problemfinder.persistence.repositories.theme_suggestions import list_suggestions

_SNIPPET_CHARS = 240


class RepresentativeSignal(BaseModel):
    id: UUID
    title: str | None
    snippet: str


class ThemeSuggestionView(BaseModel):
    """A suggestion as the dashboard sees it: evidence previews, no id lists."""

    id: UUID
    cluster_key: int
    label: str
    method: str
    size: int
    top_terms: tuple[str, ...]
    suggested_theme: str | None
    status: SuggestionStatus
    mapped_theme: str | None
    created_at: AwareDatetime
    decided_at: AwareDatetime | None
    representatives: list[RepresentativeSignal]


def theme_suggestion_views(
    session: Session, status: SuggestionStatus | None = None
) -> list[ThemeSuggestionView]:
    suggestions = list_suggestions(session, status)
    previews = _previews_for(session, suggestions)
    return [
        ThemeSuggestionView(
            **suggestion.model_dump(exclude={"member_signal_ids", "representative_signal_ids"}),
            representatives=[
                previews[signal_id]
                for signal_id in suggestion.representative_signal_ids
                if signal_id in previews
            ],
        )
        for suggestion in suggestions
    ]


def _previews_for(
    session: Session, suggestions: list[ThemeSuggestion]
) -> dict[UUID, RepresentativeSignal]:
    wanted = {
        signal_id
        for suggestion in suggestions
        for signal_id in suggestion.representative_signal_ids
    }
    if not wanted:
        return {}
    stmt = select(SignalRow.id, SignalRow.title, SignalRow.body).where(SignalRow.id.in_(wanted))
    return {
        row.id: RepresentativeSignal(id=row.id, title=row.title, snippet=row.body[:_SNIPPET_CHARS])
        for row in session.execute(stmt)
    }
