"""Annual report discovery via the documented gov.uk search and content APIs.

The search API lists the Adjudicator's Office's publications; annual reports
are recognised by their publication slug. Each publication's content JSON
names its HTML report document (the document slug is not derivable from the
year: the 2026 publication's report document is slugged 2025), so one content
fetch per report resolves the document URL to ingest plus its date hint.
"""

import re
from collections.abc import AsyncIterator

import httpx

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.cursor_state import ingested_keys
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

BASE = "https://www.gov.uk"
SEARCH_URL = (
    f"{BASE}/api/search.json?filter_organisations=the-adjudicator-s-office"
    "&fields=title,link&count=100"
)
STATE_KEY = "ingested_reports"
_PUBLICATION_RE = re.compile(
    r"^/government/publications/the-adjudicators-office-annual-report-(\d{4})$"
)


async def discover_reports(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    seen = ingested_keys(cursor, STATE_KEY)
    async with client_for(source_key, policy) as client:
        for link, year in await _annual_report_publications(client):
            if f"annual-report-{year}" in seen:
                continue
            item = await _report_work_item(client, link, year)
            if item is not None:
                yield item


async def _annual_report_publications(client: httpx.AsyncClient) -> list[tuple[str, int]]:
    response = await client.get(SEARCH_URL)
    response.raise_for_status()
    results = response.json().get("results", [])
    publications: dict[int, str] = {}
    for result in results if isinstance(results, list) else []:
        link = str(result.get("link", "")) if isinstance(result, dict) else ""
        match = _PUBLICATION_RE.match(link)
        if match:
            publications[int(match[1])] = link
    return [(link, year) for year, link in sorted(publications.items())]


async def _report_work_item(client: httpx.AsyncClient, link: str, year: int) -> WorkItem | None:
    response = await client.get(f"{BASE}/api/content{link}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    document = response.json()
    path = _report_document_path(document)
    if path is None:
        return None
    published = document.get("first_published_at") if isinstance(document, dict) else None
    return WorkItem(
        external_id=f"annual-report-{year}",
        url=f"{BASE}/api/content{path}",
        request_hints={
            "year": year,
            "page_url": f"{BASE}{path}",
            "published_at": published if isinstance(published, str) else None,
        },
    )


def _report_document_path(document: object) -> str | None:
    """The HTML report document's path; file attachments carry a content type.

    Only site-relative paths resolve against the content API. The oldest
    reports point at absolute National Archives web-archive URLs instead;
    those have no content-API document, so they are skipped.
    """
    if not isinstance(document, dict):
        return None
    details = document.get("details")
    attachments = details.get("attachments") if isinstance(details, dict) else None
    for attachment in attachments if isinstance(attachments, list) else []:
        if not isinstance(attachment, dict) or attachment.get("content_type") is not None:
            continue
        url = str(attachment.get("url", ""))
        if "annual report" in str(attachment.get("title", "")).lower() and url.startswith("/"):
            return url
    return None
