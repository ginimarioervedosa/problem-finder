"""Release discovery from the FCA's two firm-level data pages.

The firm-level page links the current release; the previous-data page links
the full history. File slugs are irregular (`...2016-h2_0.xlsx`, one absolute
`/sites/default/files/...` URL), so hrefs are always taken from the pages,
never constructed. Releases before 2016 H2 use an earlier per-product-sheet
workbook era this parser does not read, so discovery stops there.
"""

import re
from collections.abc import AsyncIterator

import httpx
from selectolax.parser import HTMLParser

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.cursor_state import ingested_keys
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

BASE = "https://www.fca.org.uk"
FIRM_LEVEL_URL = f"{BASE}/data/complaints-data/firm-level"
PREVIOUS_URL = f"{BASE}/data/complaints-data/previous-complaints-data"
STATE_KEY = "ingested_periods"
EARLIEST_MODERN_RELEASE = (2016, 2)
_FILE_RE = re.compile(r"firm-level-complaints-data-(\d{4})-h([12])[^\"/]*\.xlsx", re.IGNORECASE)


async def discover_releases(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    seen = ingested_keys(cursor, STATE_KEY)
    items: dict[str, WorkItem] = {}
    async with client_for(source_key, policy) as client:
        for page_url in (FIRM_LEVEL_URL, PREVIOUS_URL):
            for item in await _page_items(client, page_url):
                items.setdefault(item.external_id, item)
    for key in sorted(items, key=_chronological):
        if key not in seen:
            yield items[key]


def _chronological(period: str) -> tuple[int, str]:
    half, _, year = period.partition("-")
    return int(year), half


async def _page_items(client: httpx.AsyncClient, page_url: str) -> list[WorkItem]:
    response = await client.get(page_url)
    response.raise_for_status()
    items = []
    for node in HTMLParser(response.text).css("a[href]"):
        href = node.attributes.get("href") or ""
        match = _FILE_RE.search(href)
        if match is None:
            continue
        year, half = int(match[1]), int(match[2])
        if (year, half) < EARLIEST_MODERN_RELEASE:
            continue
        items.append(_work_item(f"h{half}-{year}", year, half, href, str(response.url)))
    return items


def _work_item(period: str, year: int, half: int, href: str, page_url: str) -> WorkItem:
    start, end = (
        (f"{year}-01-01", f"{year}-06-30") if half == 1 else (f"{year}-07-01", f"{year}-12-31")
    )
    return WorkItem(
        external_id=period,
        url=str(httpx.URL(page_url).join(href)),
        request_hints={
            "period": period,
            "period_start": start,
            "period_end": end,
            "page_url": page_url,
        },
    )
