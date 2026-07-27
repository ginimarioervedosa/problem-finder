"""Decision-data discovery: one page, its downloadable CSV files.

The data centre's ombudsman-decision-data page links the current cumulative
CSV under a content-hashed /media/ path that changes with every upload, so
the file slug is the work item identity. Rows inside carry stable decision
ids, which dedupe overlapping uploads at store time.
"""

from collections.abc import AsyncIterator

from selectolax.parser import HTMLParser

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.cursor_state import ingested_keys
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

BASE = "https://www.legalombudsman.org.uk"
DATA_PAGE_URL = f"{BASE}/information-centre/data-centre/ombudsman-decision-data/"
STATE_KEY = "ingested_files"


async def discover_decision_files(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    seen = ingested_keys(cursor, STATE_KEY)
    async with client_for(source_key, policy) as client:
        response = await client.get(DATA_PAGE_URL)
        response.raise_for_status()
        for path in _csv_paths(response.text):
            slug = path.rsplit("/", 1)[-1].removesuffix(".csv")
            if slug not in seen:
                yield WorkItem(
                    external_id=slug,
                    url=f"{BASE}{path}",
                    request_hints={"page_url": DATA_PAGE_URL},
                )


def _csv_paths(html: str) -> list[str]:
    paths: dict[str, None] = {}
    for node in HTMLParser(html).css("a[href]"):
        href = node.attributes.get("href") or ""
        if href.startswith("/media/") and href.lower().endswith(".csv"):
            paths[href] = None
    return list(paths)
