"""Decision discovery: walk the public search newest-first within a window.

The search serves ten results per page through a Start offset; each card
carries the decision reference, date, business, outcome, and sector, which
travel as request_hints so later stages never revisit the listing pages. The
window is fixed here for phase 2; per-source config arrives with the phase 3
scheduler work, at which point widening it becomes a config change.
"""

import re
from collections.abc import AsyncIterator
from datetime import date, datetime

import httpx
from pydantic import JsonValue
from selectolax.parser import HTMLParser, Node

from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.http import client_for
from problemfinder.sources.page_base import page_base
from problemfinder.sources.protocol import WorkItem

BASE = "https://www.financial-ombudsman.org.uk"
SEARCH_URL = f"{BASE}/businesses/resolving-complaint/ombudsman-decisions/search"
WINDOW_FROM = date(2025, 1, 1)
WINDOW_TO = date(2025, 6, 30)
_PAGE_SIZE = 10
_DRN_RE = re.compile(r"DRN-\d+", re.IGNORECASE)
_OUTCOMES = {"upheld", "not upheld"}


async def discover_decisions(source_key: str, policy: SourcePolicy) -> AsyncIterator[WorkItem]:
    """Yield one work item per decision, paging until the search runs dry.

    The walk can span thousands of pages, so discovery owns its client for
    the whole traversal rather than borrowing one per call.
    """
    async with client_for(source_key, policy) as client:
        start = 0
        while True:
            response = await client.get(SEARCH_URL, params=_params(start))
            response.raise_for_status()
            items = _page_items(response.text, str(response.url))
            if not items:
                return
            for item in items:
                yield item
            start += _PAGE_SIZE


def _params(start: int) -> dict[str, str]:
    return {
        "Sort": "date",
        "DateFrom": WINDOW_FROM.isoformat(),
        "DateTo": WINDOW_TO.isoformat(),
        "Start": str(start),
    }


def _page_items(html: str, page_url: str) -> list[WorkItem]:
    tree = HTMLParser(html)
    base_url = page_base(tree, page_url)
    cards = tree.css("a.search-result[href]")
    return [item for card in cards if (item := _card_item(card, base_url, page_url)) is not None]


def _card_item(card: Node, base_url: httpx.URL, page_url: str) -> WorkItem | None:
    href = card.attributes.get("href") or ""
    match = _DRN_RE.search(href)
    if match is None:
        return None
    decided, business, outcome = _info_parts(card.css_first(".search-result__info-main"))
    sector = card.css_first(".search-result__tag")
    hints: dict[str, JsonValue] = {
        "decision_date": decided.isoformat() if decided else None,
        "business": business,
        "outcome": outcome,
        "sector": sector.text(strip=True) if sector else None,
        "page_url": page_url,
    }
    return WorkItem(external_id=match[0].upper(), url=str(base_url.join(href)), request_hints=hints)


def _info_parts(node: Node | None) -> tuple[date | None, str | None, str | None]:
    """(decision date, business, outcome) from a card's inline metadata row."""
    if node is None:
        return None, None, None
    parts = [part.strip() for part in node.text(separator="|").split("|") if part.strip()]
    if not parts:
        return None, None, None
    decided = _decision_date(parts[0])
    rest = parts[1:] if decided else parts
    outcome = rest[-1] if rest and rest[-1].casefold() in _OUTCOMES else None
    if outcome:
        rest = rest[:-1]
    return decided, " ".join(rest) if rest else None, outcome


def _decision_date(label: str) -> date | None:
    try:
        return datetime.strptime(label, "%d %b %Y").date()
    except ValueError:
        return None
