"""Monthly buckets: aggregates land on period end, verbatims on publication."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.orm import Session

from problemfinder.queries.signal_search import SignalFilters
from problemfinder.queries.summaries import SummaryDimension
from problemfinder.queries.trends import volume_over_time
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def seeded(db_session: Session) -> Session:
    seed_signals(
        db_session,
        [
            build_aggregate(external_id="a:h1", volume=60),
            build_aggregate(
                external_id="a:h2",
                volume=40,
                period_start=date(2025, 7, 1),
                period_end=date(2025, 12, 31),
            ),
            build_verbatim(
                external_id="t3_jan",
                category="Banking & Credit",
                published_at=datetime(2025, 6, 12, tzinfo=UTC),
            ),
            build_verbatim(
                external_id="t3_none", category="Investments", published_at=None
            ),  # no effective date: must not appear in any bucket
        ],
    )
    return db_session


def test_buckets_by_month_of_the_effective_date(seeded: Session) -> None:
    points = volume_over_time(seeded, SummaryDimension.CATEGORY, SignalFilters())
    by_bucket = {(point.bucket, point.key): point for point in points}
    assert by_bucket[(date(2025, 6, 1), "Banking & Credit")].volume == 61  # 60 + 1 voice
    assert by_bucket[(date(2025, 12, 1), "Banking & Credit")].volume == 40
    assert len(points) == 2  # the dateless verbatim is excluded


def test_series_are_bounded_to_the_top_keys(seeded: Session) -> None:
    points = volume_over_time(seeded, SummaryDimension.CATEGORY, SignalFilters(), series=1)
    assert {point.key for point in points} == {"Banking & Credit"}
