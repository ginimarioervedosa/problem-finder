"""Written-evidence discovery through the official committees API.

Committee ids come from the source's options table. The cursor holds a
per-committee high-water publication date; discovery lists evidence
published on or after the later of that mark and the options window,
paging with Skip/Take. Boundary overlaps dedupe at store time.
"""

from collections.abc import AsyncIterator

import httpx
from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.config import source_options
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import WorkItem

API_BASE = "https://committees-api.parliament.uk"
PAGE_URL_TEMPLATE = "https://committees.parliament.uk/writtenevidence/{id}/"
_PAGE_SIZE = 50
_DEFAULT_COMMITTEE_IDS = [158]  # Treasury Committee
_DEFAULT_WINDOW_FROM = "2025-01-01"


def committee_ids(source_key: str) -> list[int]:
    ids = source_options(source_key).get("committee_ids")
    if not isinstance(ids, list) or not ids:
        return list(_DEFAULT_COMMITTEE_IDS)
    return [int(committee) for committee in ids if isinstance(committee, int)]


def window_from(source_key: str) -> str:
    window = source_options(source_key).get("window_from")
    return str(window) if window else _DEFAULT_WINDOW_FROM


def newest_seen(cursor: Cursor | None, committee_id: int) -> str | None:
    """The publication date of the newest submission already ingested."""
    state = cursor.state.get("newest_publication_date") if cursor else None
    value = state.get(str(committee_id)) if isinstance(state, dict) else None
    return value if isinstance(value, str) and value else None


async def discover_evidence(
    source_key: str, policy: SourcePolicy, cursor: Cursor | None
) -> AsyncIterator[WorkItem]:
    async with client_for(source_key, policy) as client:
        for committee_id in committee_ids(source_key):
            high_water = newest_seen(cursor, committee_id)
            since = max(window_from(source_key), (high_water or "")[:10])
            skip = 0
            while True:
                listing = await _page(client, committee_id, since, skip)
                items = listing.get("items")
                if not isinstance(items, list) or not items:
                    break
                for item in items:
                    if isinstance(item, dict):
                        yield _work_item(committee_id, item)
                skip += _PAGE_SIZE
                total = listing.get("totalResults")
                if isinstance(total, int) and skip >= total:
                    break


async def _page(
    client: httpx.AsyncClient, committee_id: int, since: str, skip: int
) -> dict[str, object]:
    url = (
        f"{API_BASE}/api/WrittenEvidence?CommitteeId={committee_id}"
        f"&StartDate={since}&Take={_PAGE_SIZE}&Skip={skip}"
    )
    response = await client.get(url)
    response.raise_for_status()
    listing = response.json()
    return listing if isinstance(listing, dict) else {}


def _work_item(committee_id: int, item: dict[str, object]) -> WorkItem:
    evidence_id = item.get("id")
    business = item.get("committeeBusiness")
    hints: dict[str, JsonValue] = {
        "committee_id": committee_id,
        "internal_reference": str(item.get("internalReference") or ""),
        "publication_date": str(item.get("publicationDate") or ""),
        "business_title": str(business.get("title") or "") if isinstance(business, dict) else "",
        "witnesses": _witnesses(item),
        "page_url": PAGE_URL_TEMPLATE.format(id=evidence_id),
    }
    return WorkItem(
        external_id=str(evidence_id),
        url=f"{API_BASE}/api/WrittenEvidence/{evidence_id}/Document/OriginalFormat",
        request_hints=hints,
    )


def _witnesses(item: dict[str, object]) -> list[JsonValue]:
    """Witness display names; organisations first, then any personal name."""
    names: list[JsonValue] = []
    witnesses = item.get("witnesses")
    for witness in witnesses if isinstance(witnesses, list) else []:
        if not isinstance(witness, dict):
            continue
        organisations = witness.get("organisations")
        for organisation in organisations if isinstance(organisations, list) else []:
            if isinstance(organisation, dict) and organisation.get("name"):
                names.append(str(organisation["name"]))
        if witness.get("name"):
            names.append(str(witness["name"]))
    return names
