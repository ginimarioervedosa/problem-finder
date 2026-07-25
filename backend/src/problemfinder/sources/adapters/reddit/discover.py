"""Walk each configured subreddit's /new listing, newest first.

Listing pages are the payloads: discovery reads them once to learn the
pagination boundaries, then emits one work item per page carrying its exact
query, so fetch retrieves the same slice for the immutable archive. Paging
stops once a page is entirely older than the cursor's newest post for that
subreddit, or after max_pages on a first run.
"""

from collections.abc import AsyncIterator

import httpx
from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.adapters.reddit.auth import bearer_token
from problemfinder.sources.config import source_options
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

API_BASE = "https://oauth.reddit.com"
_PAGE_LIMIT = 100
_DEFAULT_MAX_PAGES = 10


def subreddits(source_key: str) -> list[str]:
    subs = source_options(source_key).get("subreddits")
    if not isinstance(subs, list) or not subs:
        msg = f"{source_key}: sources.toml must list options.subreddits"
        raise ValueError(msg)
    return [str(sub) for sub in subs]


def max_pages(source_key: str) -> int:
    pages = source_options(source_key).get("max_pages", _DEFAULT_MAX_PAGES)
    return pages if isinstance(pages, int) else _DEFAULT_MAX_PAGES


def newest_seen(cursor: Cursor | None, subreddit: str) -> float | None:
    """The created_utc of the newest post already ingested for a subreddit."""
    state = cursor.state.get("newest_created_utc") if cursor else None
    value = state.get(subreddit) if isinstance(state, dict) else None
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


async def discover_posts(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    token = await bearer_token(source_key, policy)
    headers = {"Authorization": f"bearer {token}"}
    async with client_for(source_key, policy) as client:
        for subreddit in subreddits(source_key):
            since = newest_seen(cursor, subreddit)
            after: str | None = None
            for _ in range(max_pages(source_key)):
                url = _page_url(subreddit, after)
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                listing = response.json().get("data", {})
                created = [
                    float(child["data"]["created_utc"]) for child in listing.get("children", [])
                ]
                if not created:
                    break
                hints: dict[str, JsonValue] = {
                    "subreddit": subreddit,
                    "newest_created_utc": max(created),
                }
                yield WorkItem(
                    external_id=f"r/{subreddit}:new:{after or 'start'}",
                    url=url,
                    request_hints=hints,
                )
                after = listing.get("after")
                if after is None or (since is not None and min(created) <= since):
                    break


def _page_url(subreddit: str, after: str | None) -> str:
    params = {"limit": str(_PAGE_LIMIT), "raw_json": "1"}
    if after is not None:
        params["after"] = after
    return str(httpx.URL(f"{API_BASE}/r/{subreddit}/new", params=params))
