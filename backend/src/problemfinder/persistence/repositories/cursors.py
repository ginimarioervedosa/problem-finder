"""Per-source resume points: loaded before discover, replaced after each run."""

from sqlalchemy.orm import Session

from problemfinder.domain.cursor import Cursor
from problemfinder.persistence.mapping import cursor_to_values, row_to_cursor
from problemfinder.persistence.orm import CursorRow


def load(session: Session, source_key: str) -> Cursor | None:
    row = session.get(CursorRow, source_key)
    return row_to_cursor(row) if row else None


def save(session: Session, cursor: Cursor) -> None:
    """Insert or replace the source's single cursor row."""
    session.merge(CursorRow(**cursor_to_values(cursor)))
