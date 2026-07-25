"""Ranked themes: weightings, corroboration, latest-version reads, trend windows."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.orm import Session

from problemfinder.persistence.repositories.signal_enrichments import append_many
from problemfinder.queries.signal_search import SignalFilters, search_signals
from problemfinder.queries.themes import ranked_themes
from tests.support.builders import build_aggregate, build_enrichment, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db

ANCHOR = date(2026, 7, 25)  # recent window from 2026-01-23, previous from 2025-07-24
FRAUD = "fraud_and_scams"


@pytest.fixture
def seeded(db_session: Session) -> Session:
    recent = build_verbatim(published_at=datetime(2026, 6, 1, tzinfo=UTC))
    previous = build_verbatim(
        source_key="fos_decisions",
        external_id="DRN-1",
        published_at=datetime(2025, 10, 1, tzinfo=UTC),
    )
    old_aggregate = build_aggregate(
        period_start=date(2024, 7, 1), period_end=date(2024, 12, 31), volume=42
    )
    switched = build_verbatim(
        external_id="t3_switch", published_at=datetime(2026, 6, 15, tzinfo=UTC)
    )
    seed_signals(db_session, [recent, previous, old_aggregate, switched])
    append_many(
        db_session,
        [
            build_enrichment(recent.id, severity=0.9),
            build_enrichment(previous.id, severity=0.5),
            build_enrichment(old_aggregate.id, severity=0.25),
            build_enrichment(switched.id, theme="delays_and_service_failures", severity=0.1),
            build_enrichment(switched.id, version=2, severity=0.2),  # switched to fraud
        ],
    )
    return db_session


def test_ranked_theme_aggregates_and_weightings(seeded: Session) -> None:
    rows = ranked_themes(seeded, SignalFilters(), today=ANCHOR)
    assert [row.theme for row in rows] == [FRAUD]  # superseded theme versions don't rank
    fraud = rows[0]
    assert fraud.signals == 4
    assert fraud.volume == 45  # three voices + one 42-strong aggregate
    assert fraud.severity_weighted == pytest.approx(0.9 + 0.5 + 0.25 * 42 + 0.2)
    assert fraud.corroborating_sources == 3


def test_trend_windows_split_recent_from_previous(seeded: Session) -> None:
    fraud = ranked_themes(seeded, SignalFilters(), today=ANCHOR)[0]
    assert fraud.recent_volume == 2  # June 2026 verbatims
    assert fraud.previous_volume == 1  # October 2025 verbatim
    # the 2024 aggregate sits outside both windows but still counts in volume


def test_theme_filter_drills_to_the_producing_signals(seeded: Session) -> None:
    signals, total = search_signals(seeded, SignalFilters(theme=FRAUD))
    assert total == 4
    assert {signal.source_key for signal in signals} == {
        "reddit",
        "fos_decisions",
        "fos_complaints",
    }
    _, none_left = search_signals(seeded, SignalFilters(theme="delays_and_service_failures"))
    assert none_left == 0  # the switched signal's latest version left that theme
