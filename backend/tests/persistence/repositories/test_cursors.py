"""Cursor rows: one per source, replaced wholesale on save."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from problemfinder.domain.cursor import Cursor
from problemfinder.persistence.repositories import cursors

pytestmark = pytest.mark.db


def make_cursor(last: str, day: int = 1) -> Cursor:
    return Cursor(
        source_key="stub",
        state={"last": last},
        updated_at=datetime(2026, 7, day, tzinfo=UTC),
    )


def test_load_returns_none_for_an_unknown_source(db_session: Session) -> None:
    assert cursors.load(db_session, "nope") is None


def test_save_then_load_round_trips(db_session: Session) -> None:
    cursor = make_cursor("item-2")
    cursors.save(db_session, cursor)
    db_session.flush()
    assert cursors.load(db_session, "stub") == cursor


def test_save_replaces_the_previous_cursor(db_session: Session) -> None:
    cursors.save(db_session, make_cursor("a", day=1))
    db_session.flush()
    cursors.save(db_session, make_cursor("b", day=2))
    db_session.flush()
    assert cursors.load(db_session, "stub") == make_cursor("b", day=2)
