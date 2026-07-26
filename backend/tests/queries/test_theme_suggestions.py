"""Suggestion views: previews resolved, id lists kept out of the payload."""

import pytest
from sqlalchemy.orm import Session

from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.persistence.repositories.theme_suggestions import replace_proposed
from problemfinder.queries.theme_suggestions import theme_suggestion_views
from tests.support.builders import build_suggestion, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def seeded(db_session: Session) -> Session:
    signal = build_verbatim(body="A cryptocurrency scam drained the account overnight.")
    seed_signals(db_session, [signal])
    replace_proposed(
        db_session,
        "hdbscan:v1",
        [
            build_suggestion(
                cluster_key=0,
                member_signal_ids=(signal.id,),
                representative_signal_ids=(signal.id,),
                size=1,
            )
        ],
    )
    return db_session


def test_views_resolve_representatives_to_snippets(seeded: Session) -> None:
    views = theme_suggestion_views(seeded)
    assert len(views) == 1
    view = views[0]
    assert view.status is SuggestionStatus.PROPOSED
    assert view.representatives[0].snippet.startswith("A cryptocurrency scam")
    assert not hasattr(view, "member_signal_ids")


def test_status_filter_narrows_the_list(seeded: Session) -> None:
    assert theme_suggestion_views(seeded, SuggestionStatus.ACCEPTED) == []
    assert len(theme_suggestion_views(seeded, SuggestionStatus.PROPOSED)) == 1


def test_missing_representatives_are_dropped_not_errors(db_session: Session) -> None:
    replace_proposed(db_session, "hdbscan:v1", [build_suggestion()])  # ids never stored
    views = theme_suggestion_views(db_session)
    assert views[0].representatives == []
