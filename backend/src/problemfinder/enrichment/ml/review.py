"""The review step: a person maps each proposed cluster onto the taxonomy.

Clusters are addressed by their cluster key, which is unique among one
method's undecided proposals. Accepting maps every member signal onto a
theme name (an existing taxonomy theme, or a new name that the ranked view
picks up as-is); the enrichment runner carries accepted mappings into
versioned rows on the next `pf enrich run --recompute`.
"""

from datetime import UTC, datetime

from problemfinder.domain.theme_suggestion import SuggestionStatus, ThemeSuggestion
from problemfinder.enrichment.ml.suggest import ML_METHOD
from problemfinder.persistence.engine import session_scope
from problemfinder.persistence.repositories import theme_suggestions


class UnknownClusterError(LookupError):
    """No undecided proposal carries this cluster key."""

    def __init__(self, cluster_key: int) -> None:
        super().__init__(
            f"no proposed {ML_METHOD} suggestion has cluster key {cluster_key}; "
            "run `pf ml suggestions` to list the current proposals"
        )


def list_reviews(status: SuggestionStatus | None = None) -> list[ThemeSuggestion]:
    with session_scope() as session:
        return theme_suggestions.list_suggestions(session, status)


def accept(cluster_key: int, theme: str | None = None) -> ThemeSuggestion:
    """Map one proposed cluster onto `theme` (default: its suggested match)."""
    return _decide(cluster_key, SuggestionStatus.ACCEPTED, theme)


def reject(cluster_key: int) -> ThemeSuggestion:
    return _decide(cluster_key, SuggestionStatus.REJECTED, None)


def _decide(cluster_key: int, status: SuggestionStatus, theme: str | None) -> ThemeSuggestion:
    with session_scope() as session:
        proposal = theme_suggestions.find_proposed(session, ML_METHOD, cluster_key)
        if proposal is None:
            raise UnknownClusterError(cluster_key)
        mapped = None
        if status is SuggestionStatus.ACCEPTED:
            mapped = theme or proposal.suggested_theme or proposal.label
        decided = theme_suggestions.decide(
            session, proposal.id, status, mapped, datetime.now(tz=UTC)
        )
        assert decided is not None  # the row was just read inside this transaction
        return decided
