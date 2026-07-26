"""Theme suggestions proposed by clustering, for the dashboard."""

from fastapi import APIRouter

from problemfinder.api.dependencies import SessionDep
from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.queries.theme_suggestions import ThemeSuggestionView, theme_suggestion_views

router = APIRouter(prefix="/api/theme-suggestions", tags=["theme-suggestions"])


@router.get("")
def suggestions(
    session: SessionDep, status: SuggestionStatus | None = None
) -> list[ThemeSuggestionView]:
    return theme_suggestion_views(session, status)
