"""Grouped volumes: aggregates count at volume, verbatims as one voice each."""

import pytest
from sqlalchemy.orm import Session

from problemfinder.queries.signal_search import SignalFilters
from problemfinder.queries.summaries import SummaryDimension, volume_by
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def seeded(db_session: Session) -> Session:
    seed_signals(
        db_session,
        [
            build_aggregate(external_id="a:banking", volume=60, upheld_share=0.5),
            build_aggregate(
                external_id="b:banking", firm_name="Beta", volume=40, upheld_share=0.25
            ),
            build_aggregate(
                external_id="a:investments", category="Investments", volume=10, upheld_share=None
            ),
            build_verbatim(body="fee shock", category="Investments"),
        ],
    )
    return db_session


def test_category_volumes_and_weighted_upheld(seeded: Session) -> None:
    rows = {row.key: row for row in volume_by(seeded, SummaryDimension.CATEGORY, SignalFilters())}
    banking = rows["Banking & Credit"]
    assert banking.volume == 100
    assert banking.signals == 2
    assert banking.upheld_share == pytest.approx(0.4)  # (60*0.5 + 40*0.25) / 100
    investments = rows["Investments"]
    assert investments.volume == 11  # 10 aggregate + 1 verbatim voice
    assert investments.upheld_share is None


def test_firm_dimension_respects_filters(seeded: Session) -> None:
    rows = volume_by(seeded, SummaryDimension.FIRM, SignalFilters(category="Banking & Credit"))
    assert [(row.key, row.volume) for row in rows] == [("Firm", 60), ("Beta", 40)]
