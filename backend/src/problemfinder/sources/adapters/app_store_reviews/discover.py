"""Walk each configured app's most-recent reviews feed, newest first.

Feed pages are the payloads: discovery reads them once to learn where the
new reviews stop, then emits one work item per page carrying its exact URL,
so fetch retrieves the same slice for the immutable archive. Paging stops
at the feed's ten-page cap, on an empty page, or once a page is entirely
older than the cursor's newest review for that app. Timestamps normalise
to UTC before comparison because the feed serves Pacific-time offsets.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.adapters.app_store_reviews.feed import feed_entries, updated_at
from problemfinder.sources.config import source_options
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

FEED_URL_TEMPLATE = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortby=mostrecent/page={page}/json"
)
STATE_KEY = "newest_review_updated"
_FEED_PAGE_CAP = 10


def configured_apps(source_key: str) -> dict[str, str]:
    """App id -> firm label, from the source's options table."""
    apps = source_options(source_key).get("apps")
    if not isinstance(apps, dict) or not apps:
        msg = f"{source_key}: sources.toml must map options.apps ids to firm names"
        raise ValueError(msg)
    return {str(app_id): str(firm) for app_id, firm in apps.items()}


def country(source_key: str) -> str:
    value = source_options(source_key).get("country", "gb")
    return str(value)


def newest_seen(cursor: Cursor | None, app_id: str) -> str | None:
    state = cursor.state.get(STATE_KEY) if cursor else None
    value = state.get(app_id) if isinstance(state, dict) else None
    return value if isinstance(value, str) and value else None


async def discover_review_pages(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    store = country(source_key)
    async with client_for(source_key, policy) as client:
        for app_id, firm in configured_apps(source_key).items():
            since = newest_seen(cursor, app_id)
            for page in range(1, _FEED_PAGE_CAP + 1):
                url = FEED_URL_TEMPLATE.format(country=store, app_id=app_id, page=page)
                response = await client.get(url)
                response.raise_for_status()
                updates = [
                    stamp
                    for entry in feed_entries(response.json())
                    if (stamp := _utc(updated_at(entry))) is not None
                ]
                if not updates:
                    break
                hints: dict[str, JsonValue] = {
                    "app_id": app_id,
                    "firm": firm,
                    "country": store,
                    "newest_updated": max(updates),
                }
                yield WorkItem(
                    external_id=f"{store}:{app_id}:page-{page}", url=url, request_hints=hints
                )
                if since is not None and min(updates) <= since:
                    break


def _utc(stamp: str | None) -> str | None:
    if stamp is None:
        return None
    try:
        return datetime.fromisoformat(stamp).astimezone(UTC).isoformat()
    except ValueError:
        return None
