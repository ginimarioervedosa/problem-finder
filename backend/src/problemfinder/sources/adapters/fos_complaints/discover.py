"""Release discovery: index page, plus forward probing for new periods.

The FOS lists past releases on one index page; the newest release lives on its
own page not always linked there. We therefore probe the deterministic slug
pattern a few periods past the newest one found, so new publications are
picked up without code changes.
"""

import re
from datetime import UTC, date, datetime

import httpx
from selectolax.parser import HTMLParser

from problemfinder.sources.protocol import WorkItem

BASE = "https://www.financial-ombudsman.org.uk"
INDEX_URL = f"{BASE}/data-insight/previous-complaints-data"
RELEASE_PATH = f"{BASE}/data-insight/our-insight/half-yearly-complaints-data"
_RELEASE_RE = re.compile(r"half-yearly-complaints-data-(h[12])-(\d{4})")
_PUBLISHED_RE = re.compile(r"Date published:\s*(\d{1,2} \w+ \d{4})")
_PROBE_AHEAD = 3


def _period_bounds(half: str, year: int) -> tuple[date, date]:
    if half == "h1":
        return date(year, 1, 1), date(year, 6, 30)
    return date(year, 7, 1), date(year, 12, 31)


def _next_period(half: str, year: int) -> tuple[str, int]:
    return ("h2", year) if half == "h1" else ("h1", year + 1)


async def discover_releases(client: httpx.AsyncClient) -> list[WorkItem]:
    periods = await _known_periods(client)
    items: list[WorkItem] = []
    for half, year in sorted(periods, key=lambda p: (p[1], p[0])):
        item = await _release_work_item(client, half, year)
        if item is not None:
            items.append(item)
    return items


async def _known_periods(client: httpx.AsyncClient) -> set[tuple[str, int]]:
    response = await client.get(INDEX_URL)
    response.raise_for_status()
    found = {(m[0], int(m[1])) for m in _RELEASE_RE.findall(response.text)}
    if not found:
        return found
    probe = max(found, key=lambda p: (p[1], p[0]))
    for _ in range(_PROBE_AHEAD):
        probe = _next_period(*probe)
        found.add(probe)
    return found


async def _release_work_item(client: httpx.AsyncClient, half: str, year: int) -> WorkItem | None:
    page_url = f"{RELEASE_PATH}-{half}-{year}"
    response = await client.get(page_url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    file_url = _business_data_href(response.text)
    if file_url is None:
        return None
    start, end = _period_bounds(half, year)
    published = _published_at(response.text)
    return WorkItem(
        external_id=f"{half}-{year}",
        url=file_url,
        request_hints={
            "period": f"{half}-{year}",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "page_url": page_url,
            "published_at": published.isoformat() if published else None,
        },
    )


def _business_data_href(html: str) -> str | None:
    for node in HTMLParser(html).css("a[href]"):
        href = node.attributes.get("href") or ""
        if "business-complaints-data" in href.lower() and href.lower().endswith(".xlsx"):
            return href if href.startswith("http") else f"{BASE}{href}"
    return None


def _published_at(html: str) -> datetime | None:
    match = _PUBLISHED_RE.search(html)
    if not match:
        return None
    try:
        return datetime.strptime(match[1], "%d %B %Y").replace(tzinfo=UTC)
    except ValueError:
        return None
