"""Release discovery, two-pronged.

The previous-data index page links workbook files directly for the older
half-years (2009 to 2020). Later releases each have their own page; the site's
sitemap.xml is the canonical list of those pages, so new publications are
picked up without code changes. Every page fetch goes through the same
rate-limited, identified client as the file downloads.
"""

import re
from datetime import UTC, datetime

import httpx
from selectolax.parser import HTMLParser

from problemfinder.sources.page_base import page_base
from problemfinder.sources.protocol import WorkItem

BASE = "https://www.financial-ombudsman.org.uk"
INDEX_URL = f"{BASE}/data-insight/previous-complaints-data"
SITEMAP_URL = f"{BASE}/sitemap.xml"
_FILE_RE = re.compile(r"business-complaints-data-h?([12])-(\d{4})\.xlsx", re.IGNORECASE)
_RELEASE_LOC_RE = re.compile(r"<loc>([^<]*half-yearly-complaints-data-h([12])-(\d{4}))\s*</loc>")
_PUBLISHED_RE = re.compile(r"Date published:\s*(\d{1,2} \w+ \d{4})")


async def discover_releases(client: httpx.AsyncClient) -> list[WorkItem]:
    items = {item.external_id: item for item in await _index_file_items(client)}
    for page_path, half, year in await _sitemap_release_pages(client):
        item = await _release_work_item(client, page_path, half, year)
        if item is not None:
            items[item.external_id] = item
    return sorted(items.values(), key=_chronological)


def _chronological(item: WorkItem) -> tuple[int, str]:
    half, _, year = item.external_id.partition("-")
    return int(year), half


def _period_bounds(half: str, year: int) -> tuple[str, str]:
    if half == "h1":
        return f"{year}-01-01", f"{year}-06-30"
    return f"{year}-07-01", f"{year}-12-31"


def _work_item(
    half: str, year: int, file_url: str, page_url: str, published: datetime | None
) -> WorkItem:
    start, end = _period_bounds(half, year)
    return WorkItem(
        external_id=f"{half}-{year}",
        url=file_url,
        request_hints={
            "period": f"{half}-{year}",
            "period_start": start,
            "period_end": end,
            "page_url": page_url,
            "published_at": published.isoformat() if published else None,
        },
    )


async def _index_file_items(client: httpx.AsyncClient) -> list[WorkItem]:
    response = await client.get(INDEX_URL)
    response.raise_for_status()
    tree = HTMLParser(response.text)
    base_url = page_base(tree, str(response.url))
    items: list[WorkItem] = []
    for node in tree.css("a[href]"):
        href = node.attributes.get("href") or ""
        match = _FILE_RE.search(href)
        if match is None:
            continue
        half, year = f"h{match[1]}", int(match[2])
        items.append(_work_item(half, year, str(base_url.join(href)), str(response.url), None))
    return items


async def _sitemap_release_pages(client: httpx.AsyncClient) -> list[tuple[str, str, int]]:
    """(page path, half, year) per release page listed in the sitemap.

    Sitemap hosts are occasionally malformed on this site, so only the path is
    trusted; pages are fetched against BASE.
    """
    response = await client.get(SITEMAP_URL)
    response.raise_for_status()
    pages: dict[str, tuple[str, str, int]] = {}
    for loc, half_digit, year in _RELEASE_LOC_RE.findall(response.text):
        half = f"h{half_digit}"
        pages[f"{half}-{year}"] = (httpx.URL(loc).path, half, int(year))
    return sorted(pages.values(), key=lambda page: (page[2], page[1]))


async def _release_work_item(
    client: httpx.AsyncClient, page_path: str, half: str, year: int
) -> WorkItem | None:
    page_url = f"{BASE}{page_path}"
    response = await client.get(page_url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    file_url = _business_data_href(response.text, page_url)
    if file_url is None:
        return None
    return _work_item(half, year, file_url, page_url, _published_at(response.text))


def _business_data_href(html: str, page_url: str) -> str | None:
    tree = HTMLParser(html)
    base_url = page_base(tree, page_url)
    for node in tree.css("a[href]"):
        href = node.attributes.get("href") or ""
        if "business-complaints-data" in href.lower() and href.lower().endswith(".xlsx"):
            return str(base_url.join(href))
    return None


def _published_at(html: str) -> datetime | None:
    match = _PUBLISHED_RE.search(html)
    if not match:
        return None
    try:
        return datetime.strptime(match[1], "%d %B %Y").replace(tzinfo=UTC)
    except ValueError:
        return None
