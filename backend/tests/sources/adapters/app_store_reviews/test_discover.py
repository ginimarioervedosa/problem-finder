"""Discovery: page walking, UTC normalisation, and the cursor stop rule."""

import json
from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import RateLimit
from problemfinder.sources.adapters.app_store_reviews import discover
from problemfinder.sources.adapters.app_store_reviews.adapter import AppStoreReviewsSource
from problemfinder.sources.adapters.app_store_reviews.discover import discover_review_pages
from problemfinder.sources.protocol import WorkItem

FAST_POLICY = AppStoreReviewsSource.policy.model_copy(
    update={"rate_limit": RateLimit(requests=1000, per_seconds=0.001)}
)


def feed_page(updated: list[str]) -> str:
    entries = [
        {"id": {"label": f"r{index}"}, "updated": {"label": stamp}}
        for index, stamp in enumerate(updated)
    ]
    return json.dumps({"feed": {"entry": entries}})


def page_url(page: int) -> str:
    return discover.FEED_URL_TEMPLATE.format(country="gb", app_id="111", page=page)


@pytest.fixture
def app_store(monkeypatch: pytest.MonkeyPatch) -> Generator[respx.MockRouter]:
    monkeypatch.setattr(
        discover, "source_options", lambda key: {"apps": {"111": "TestBank"}, "country": "gb"}
    )
    with respx.mock(assert_all_called=False) as router:
        router.get(page_url(1)).mock(
            return_value=httpx.Response(
                200, text=feed_page(["2026-07-25T10:00:00-07:00", "2026-07-25T09:00:00-07:00"])
            )
        )
        router.get(page_url(2)).mock(
            return_value=httpx.Response(200, text=feed_page(["2026-07-20T10:00:00-07:00"]))
        )
        router.get(page_url(3)).mock(
            return_value=httpx.Response(200, text=json.dumps({"feed": {}}))
        )
        yield router


async def collect(cursor: Cursor | None) -> list[WorkItem]:
    return [item async for item in discover_review_pages("app_store_reviews", FAST_POLICY, cursor)]


async def test_walks_pages_until_the_feed_runs_dry(app_store: respx.MockRouter) -> None:
    items = await collect(None)
    assert [item.external_id for item in items] == ["gb:111:page-1", "gb:111:page-2"]


async def test_hints_carry_the_firm_and_utc_normalised_high_water(
    app_store: respx.MockRouter,
) -> None:
    first = (await collect(None))[0]
    assert first.request_hints["firm"] == "TestBank"
    assert first.request_hints["newest_updated"] == "2026-07-25T17:00:00+00:00"


async def test_stops_at_the_cursor_high_water_mark(app_store: respx.MockRouter) -> None:
    cursor = Cursor(
        source_key="app_store_reviews",
        state={"newest_review_updated": {"111": "2026-07-25T16:30:00+00:00"}},
        updated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    items = await collect(cursor)
    assert [item.external_id for item in items] == ["gb:111:page-1"]
    assert not any(call.request.url == page_url(3) for call in app_store.calls)
