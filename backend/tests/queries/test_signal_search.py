"""Search filters, pagination, and detail lookup against real Postgres."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from problemfinder.domain.signal import SignalKind
from problemfinder.queries.signal_search import SignalFilters, get_signal, search_signals
from tests.support.builders import build_aggregate, build_verbatim
from tests.support.seeding import seed_signals

pytestmark = pytest.mark.db


@pytest.fixture
def seeded(db_session: Session) -> Session:
    seed_signals(
        db_session,
        [
            build_aggregate(
                external_id="h1-2025:alpha:banking", firm_name="Alpha Bank", volume=100
            ),
            build_aggregate(
                external_id="h1-2025:alpha:investments",
                firm_name="Alpha Bank",
                category="Investments",
                volume=7,
            ),
            build_aggregate(
                external_id="h2-2024:beta:banking",
                firm_name="Beta Wealth",
                period_start=date(2024, 7, 1),
                period_end=date(2024, 12, 31),
                volume=30,
            ),
            build_verbatim(body="my SIPP transfer stalled for months"),
        ],
    )
    return db_session


def test_no_filters_returns_everything_with_total(seeded: Session) -> None:
    items, total = search_signals(seeded, SignalFilters())
    assert total == 4
    assert len(items) == 4


def test_firm_filter_is_substring_and_case_insensitive(seeded: Session) -> None:
    items, total = search_signals(seeded, SignalFilters(firm="alpha"))
    assert total == 2
    assert all(item.firm_name == "Alpha Bank" for item in items)


def test_kind_and_category_filters(seeded: Session) -> None:
    _, verbatims = search_signals(seeded, SignalFilters(kind=SignalKind.VERBATIM))
    assert verbatims == 1
    _, investments = search_signals(seeded, SignalFilters(category="Investments"))
    assert investments == 1


def test_period_filter_uses_effective_date(seeded: Session) -> None:
    items, total = search_signals(seeded, SignalFilters(period_from=date(2025, 1, 1)))
    assert total == 3
    assert {item.external_id for item in items} >= {"h1-2025:alpha:banking"}


def test_pagination_is_stable(seeded: Session) -> None:
    first, total = search_signals(seeded, SignalFilters(), limit=2, offset=0)
    second, _ = search_signals(seeded, SignalFilters(), limit=2, offset=2)
    assert total == 4
    assert {i.id for i in first} & {i.id for i in second} == set()


def test_detail_lookup(seeded: Session) -> None:
    [first], _ = search_signals(seeded, SignalFilters(), limit=1)
    assert get_signal(seeded, str(first.id)) == first
    assert get_signal(seeded, "00000000-0000-0000-0000-000000000000") is None


def test_search_matches_stemmed_words_in_the_body(seeded: Session) -> None:
    items, total = search_signals(seeded, SignalFilters(search="transfers stalling"))
    assert total == 1
    assert items[0].kind is SignalKind.VERBATIM


def test_search_covers_titles_too(seeded: Session) -> None:
    _, total = search_signals(seeded, SignalFilters(search="complaints"))
    assert total == 3  # every aggregate title mentions complaints


def test_search_supports_phrases_and_finds_nothing_gracefully(seeded: Session) -> None:
    _, phrase = search_signals(seeded, SignalFilters(search='"SIPP transfer"'))
    assert phrase == 1
    _, none = search_signals(seeded, SignalFilters(search="mortgage"))
    assert none == 0


def test_search_composes_with_other_filters(seeded: Session) -> None:
    filters = SignalFilters(search="complaints", firm="Beta")
    items, total = search_signals(seeded, filters)
    assert total == 1
    assert items[0].firm_name == "Beta Wealth"
