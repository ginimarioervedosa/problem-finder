"""Discovery: OAuth, pagination, and the cursor stop condition."""

import json
from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import RateLimit
from problemfinder.settings import get_settings
from problemfinder.sources.adapters.reddit import auth, discover
from problemfinder.sources.adapters.reddit.adapter import RedditSource
from problemfinder.sources.adapters.reddit.auth import RedditCredentialsError, bearer_token
from problemfinder.sources.adapters.reddit.discover import discover_posts
from problemfinder.sources.protocol import WorkItem

FAST_POLICY = RedditSource.policy.model_copy(
    update={"rate_limit": RateLimit(requests=1000, per_seconds=0.001)}
)


def listing(after: str | None, created: list[float]) -> str:
    children = [
        {"kind": "t3", "data": {"name": f"t3_{int(stamp)}", "created_utc": stamp}}
        for stamp in created
    ]
    return json.dumps({"kind": "Listing", "data": {"after": after, "children": children}})


@pytest.fixture
def reddit_env(monkeypatch: pytest.MonkeyPatch) -> Generator[respx.MockRouter]:
    monkeypatch.setenv("PF_REDDIT_CLIENT_ID", "test-client")
    monkeypatch.setenv("PF_REDDIT_CLIENT_SECRET", "test-secret")
    get_settings.cache_clear()
    monkeypatch.setattr(auth, "_cached", None)
    monkeypatch.setattr(
        discover, "source_options", lambda key: {"subreddits": ["testsub"], "max_pages": 5}
    )
    with respx.mock(assert_all_called=False) as router:
        router.post(auth.TOKEN_URL).mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok", "token_type": "bearer", "expires_in": 3600}
            )
        )
        router.get(f"{discover.API_BASE}/r/testsub/new", params={"limit": "100"}).mock(
            side_effect=lambda request: httpx.Response(
                200,
                text=listing("t3_200", [300.0, 200.0])
                if "after" not in dict(request.url.params)
                else listing(None, [100.0, 50.0]),
            )
        )
        yield router
    get_settings.cache_clear()


async def collect(cursor: Cursor | None) -> list[WorkItem]:
    return [item async for item in discover_posts("reddit_test", FAST_POLICY, cursor)]


def make_cursor(newest: float) -> Cursor:
    return Cursor(
        source_key="reddit",
        state={"newest_created_utc": {"testsub": newest}},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


async def test_first_run_pages_until_the_listing_runs_dry(reddit_env: respx.MockRouter) -> None:
    items = await collect(None)
    assert [item.external_id for item in items] == [
        "r/testsub:new:start",
        "r/testsub:new:t3_200",
    ]
    assert items[0].request_hints == {"subreddit": "testsub", "newest_created_utc": 300.0}
    assert "limit=100" in str(items[0].url)


async def test_requests_carry_the_bearer_token(reddit_env: respx.MockRouter) -> None:
    await collect(None)
    listing_calls = [call for call in reddit_env.calls if call.request.method == "GET"]
    assert all(call.request.headers["Authorization"] == "bearer tok" for call in listing_calls)


async def test_paging_stops_once_a_page_is_older_than_the_cursor(
    reddit_env: respx.MockRouter,
) -> None:
    items = await collect(make_cursor(250.0))
    assert [item.external_id for item in items] == ["r/testsub:new:start"]


async def test_missing_credentials_fail_loudly(
    reddit_env: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PF_REDDIT_CLIENT_ID")
    get_settings.cache_clear()
    with pytest.raises(RedditCredentialsError):
        await bearer_token("reddit_test", FAST_POLICY)
