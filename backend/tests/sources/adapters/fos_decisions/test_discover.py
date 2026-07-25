"""Discovery: card extraction, base-tag URL resolution, and pagination."""

from collections.abc import Generator
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.source_policy import RateLimit
from problemfinder.sources.adapters.fos_decisions import discover
from problemfinder.sources.adapters.fos_decisions.adapter import FosDecisionsSource
from problemfinder.sources.adapters.fos_decisions.discover import (
    SEARCH_URL,
    decision_window,
    discover_decisions,
)
from problemfinder.sources.protocol import WorkItem

FIXTURE = Path(__file__).parent / "fixtures" / "decisions-search-page.html"
EMPTY_PAGE = """
<html><head><base href="https://www.financial-ombudsman.org.uk/"></head>
<body><ul class="search-results" role="list"></ul></body></html>
"""
# A distinct key and a loose limit keep the shared token bucket out of tests.
FAST_POLICY = FosDecisionsSource.policy.model_copy(
    update={"rate_limit": RateLimit(requests=1000, per_seconds=0.001)}
)


@pytest.fixture
def fos_search() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(SEARCH_URL, params={"Start": "0"}).mock(
            return_value=httpx.Response(200, text=FIXTURE.read_text())
        )
        router.get(SEARCH_URL, params={"Start": "10"}).mock(
            return_value=httpx.Response(200, text=EMPTY_PAGE)
        )
        yield router


WINDOW = (date(2025, 1, 1), date(2025, 6, 30))


async def collect(router: respx.MockRouter) -> list[WorkItem]:
    return [item async for item in discover_decisions("fos_decisions_test", FAST_POLICY, WINDOW)]


async def test_yields_one_item_per_card_until_the_search_runs_dry(
    fos_search: respx.MockRouter,
) -> None:
    items = await collect(fos_search)
    assert [item.external_id for item in items] == ["DRN-4966044", "DRN-5658919", "DRN-5159074"]
    assert len(fos_search.calls) == 2  # the empty page stops pagination


async def test_pdf_urls_resolve_against_the_base_tag(fos_search: respx.MockRouter) -> None:
    items = await collect(fos_search)
    assert str(items[0].url) == "https://www.financial-ombudsman.org.uk/decision/DRN-4966044.pdf"


async def test_cards_carry_listing_metadata_as_hints(fos_search: respx.MockRouter) -> None:
    revolut, novia, _ = await collect(fos_search)
    assert revolut.request_hints["decision_date"] == "2025-06-30"
    assert revolut.request_hints["business"] == "Revolut Ltd"
    assert revolut.request_hints["outcome"] == "Not upheld"
    assert revolut.request_hints["sector"] == "Banking and Payments"
    assert novia.request_hints["outcome"] == "Upheld"
    assert novia.request_hints["business"] == "Novia Financial Plc"


async def test_requests_stay_within_the_configured_window(fos_search: respx.MockRouter) -> None:
    await collect(fos_search)
    first = httpx.URL(str(fos_search.calls[0].request.url))
    assert first.params["DateFrom"] == "2025-01-01"
    assert first.params["DateTo"] == "2025-06-30"
    assert first.params["Sort"] == "date"
    second = httpx.URL(str(fos_search.calls[1].request.url))
    assert second.params["Start"] == "10"


def make_cursor(latest: str | None) -> Cursor:
    state = {"latest_decision_date": latest}
    return Cursor(
        source_key="fos_decisions", state=state, updated_at=datetime(2026, 7, 1, tzinfo=UTC)
    )


def test_window_resumes_from_the_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(discover, "source_options", lambda key: {})
    resumed = decision_window("fos_decisions", make_cursor("2025-03-15"))
    assert resumed == (date(2025, 3, 15), date(2025, 6, 30))


def test_window_never_starts_before_the_configured_from(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(discover, "source_options", lambda key: {})
    early = decision_window("fos_decisions", make_cursor("2024-11-01"))
    assert early == (date(2025, 1, 1), date(2025, 6, 30))
    assert decision_window("fos_decisions", None) == (date(2025, 1, 1), date(2025, 6, 30))
    assert decision_window("fos_decisions", make_cursor(None))[0] == date(2025, 1, 1)
