"""Suggestion rows: proposals replaced wholesale, decisions surviving them."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from problemfinder.domain.theme_suggestion import SuggestionStatus
from problemfinder.persistence.repositories import theme_suggestions
from tests.support.builders import build_suggestion

pytestmark = pytest.mark.db

DECIDED_AT = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def test_replace_proposed_swaps_undecided_rows_only(db_session: Session) -> None:
    kept = build_suggestion(cluster_key=1)
    dropped = build_suggestion(cluster_key=2)
    theme_suggestions.replace_proposed(db_session, "hdbscan:v1", [kept, dropped])
    theme_suggestions.decide(
        db_session, kept.id, SuggestionStatus.ACCEPTED, "fraud_and_scams", DECIDED_AT
    )
    fresh = build_suggestion(cluster_key=3)
    removed, inserted = theme_suggestions.replace_proposed(db_session, "hdbscan:v1", [fresh])
    assert (removed, inserted) == (1, 1)
    remaining = {s.cluster_key for s in theme_suggestions.list_suggestions(db_session)}
    assert remaining == {1, 3}


def test_list_suggestions_filters_by_status(db_session: Session) -> None:
    suggestion = build_suggestion()
    theme_suggestions.replace_proposed(db_session, "hdbscan:v1", [suggestion])
    assert theme_suggestions.list_suggestions(db_session, SuggestionStatus.ACCEPTED) == []
    proposed = theme_suggestions.list_suggestions(db_session, SuggestionStatus.PROPOSED)
    assert [s.id for s in proposed] == [suggestion.id]


def test_decide_records_status_theme_and_time(db_session: Session) -> None:
    suggestion = build_suggestion()
    theme_suggestions.replace_proposed(db_session, "hdbscan:v1", [suggestion])
    decided = theme_suggestions.decide(
        db_session, suggestion.id, SuggestionStatus.ACCEPTED, "fraud_and_scams", DECIDED_AT
    )
    assert decided is not None
    assert decided.status is SuggestionStatus.ACCEPTED
    assert decided.mapped_theme == "fraud_and_scams"
    assert decided.decided_at == DECIDED_AT


def test_decide_returns_none_for_an_unknown_id(db_session: Session) -> None:
    assert (
        theme_suggestions.decide(db_session, uuid4(), SuggestionStatus.REJECTED, None, DECIDED_AT)
        is None
    )


def test_accepted_assignments_map_members_and_later_decisions_win(db_session: Session) -> None:
    shared = uuid4()
    first = build_suggestion(cluster_key=1, member_signal_ids=(shared, uuid4()))
    second = build_suggestion(cluster_key=2, member_signal_ids=(shared,))
    rejected = build_suggestion(cluster_key=3)
    theme_suggestions.replace_proposed(db_session, "hdbscan:v1", [first, second, rejected])
    theme_suggestions.decide(
        db_session, first.id, SuggestionStatus.ACCEPTED, "charges_and_fees", DECIDED_AT
    )
    theme_suggestions.decide(
        db_session,
        second.id,
        SuggestionStatus.ACCEPTED,
        "fraud_and_scams",
        datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
    )
    theme_suggestions.decide(db_session, rejected.id, SuggestionStatus.REJECTED, None, DECIDED_AT)
    assignments = theme_suggestions.accepted_assignments(db_session)
    assert assignments[shared].theme == "fraud_and_scams"
    assert assignments[shared].method == "hdbscan:v1"
    assert len(assignments) == 2  # shared + first's other member; rejected contributes none
