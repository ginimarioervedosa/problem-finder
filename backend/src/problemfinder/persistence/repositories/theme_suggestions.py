"""Theme suggestion rows: propose wholesale, decide one at a time.

Reclustering replaces every undecided row for its method; accepted and
rejected rows survive because they carry review decisions. Accepted rows are
the source of the per-signal ML theme assignments the enrichment runner
folds in, with the latest decision winning where clusters overlap.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from problemfinder.domain.theme_suggestion import (
    MlThemeAssignment,
    SuggestionStatus,
    ThemeSuggestion,
)
from problemfinder.persistence.mapping import row_to_suggestion, suggestion_to_values
from problemfinder.persistence.orm import ThemeSuggestionRow


def replace_proposed(
    session: Session, method: str, suggestions: list[ThemeSuggestion]
) -> tuple[int, int]:
    """Swap the undecided proposals for `method`. Returns (removed, inserted)."""
    undecided = (
        ThemeSuggestionRow.method == method,
        ThemeSuggestionRow.status == SuggestionStatus.PROPOSED.value,
    )
    removed = (
        session.scalar(select(func.count()).select_from(ThemeSuggestionRow).where(*undecided)) or 0
    )
    session.execute(delete(ThemeSuggestionRow).where(*undecided))
    if suggestions:
        values = [suggestion_to_values(suggestion) for suggestion in suggestions]
        session.execute(insert(ThemeSuggestionRow).values(values))
    return removed, len(suggestions)


def list_suggestions(
    session: Session, status: SuggestionStatus | None = None
) -> list[ThemeSuggestion]:
    """Every suggestion (optionally one status), largest clusters first."""
    stmt = select(ThemeSuggestionRow).order_by(
        ThemeSuggestionRow.size.desc(), ThemeSuggestionRow.cluster_key
    )
    if status is not None:
        stmt = stmt.where(ThemeSuggestionRow.status == status.value)
    return [row_to_suggestion(row) for row in session.execute(stmt).scalars()]


def find_proposed(session: Session, method: str, cluster_key: int) -> ThemeSuggestion | None:
    """The undecided proposal for one cluster of one method, if it exists."""
    stmt = select(ThemeSuggestionRow).where(
        ThemeSuggestionRow.method == method,
        ThemeSuggestionRow.cluster_key == cluster_key,
        ThemeSuggestionRow.status == SuggestionStatus.PROPOSED.value,
    )
    row = session.execute(stmt).scalar_one_or_none()
    return row_to_suggestion(row) if row else None


def decide(
    session: Session,
    suggestion_id: UUID,
    status: SuggestionStatus,
    mapped_theme: str | None,
    decided_at: datetime,
) -> ThemeSuggestion | None:
    """Record one review decision; None when the id is unknown."""
    session.execute(
        update(ThemeSuggestionRow)
        .where(ThemeSuggestionRow.id == suggestion_id)
        .values(status=status.value, mapped_theme=mapped_theme, decided_at=decided_at)
    )
    row = session.get(ThemeSuggestionRow, suggestion_id)
    return row_to_suggestion(row) if row else None


def accepted_assignments(session: Session) -> dict[UUID, MlThemeAssignment]:
    """signal id -> accepted theme mapping; later decisions win overlaps."""
    stmt = (
        select(ThemeSuggestionRow)
        .where(ThemeSuggestionRow.status == SuggestionStatus.ACCEPTED.value)
        .order_by(ThemeSuggestionRow.decided_at)
    )
    assignments: dict[UUID, MlThemeAssignment] = {}
    for row in session.execute(stmt).scalars():
        if row.mapped_theme is None:
            continue
        assignment = MlThemeAssignment(theme=row.mapped_theme, method=row.method)
        for member in row.member_signal_ids:
            assignments[UUID(member)] = assignment
    return assignments
