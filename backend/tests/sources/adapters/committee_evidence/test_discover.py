"""Discovery: listing pagination, hints, and the cursor high-water mark."""

from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.adapters.committee_evidence.adapter import CommitteeEvidenceSource
from problemfinder.sources.adapters.committee_evidence.discover import (
    API_BASE,
    discover_evidence,
)
from problemfinder.sources.protocol import WorkItem

POLICY = CommitteeEvidenceSource.policy

PAGE_ONE = {
    "totalResults": 2,
    "items": [
        {
            "id": 167697,
            "internalReference": "BoEMPR0014",
            "publicationDate": "2026-06-24T10:15:00",
            "committeeBusiness": {"title": "Bank of England Monetary Policy Reports"},
            "witnesses": [{"name": "Jane Example", "organisations": [{"name": "UK Finance"}]}],
        },
        {
            "id": 165375,
            "internalReference": "SLTG0229",
            "publicationDate": "2026-05-28T09:30:00",
            "committeeBusiness": None,
            "witnesses": [],
        },
    ],
}


async def discovered(cursor: Cursor | None = None) -> list[WorkItem]:
    return [item async for item in discover_evidence("committee_evidence", POLICY, cursor)]


@pytest.fixture
def committees_api() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(url__startswith=f"{API_BASE}/api/WrittenEvidence").mock(
            return_value=httpx.Response(200, json=PAGE_ONE)
        )
        yield router


async def test_each_listed_submission_becomes_one_work_item(
    committees_api: respx.MockRouter,
) -> None:
    items = await discovered()
    assert [item.external_id for item in items] == ["167697", "165375"]
    first = items[0]
    assert str(first.url) == f"{API_BASE}/api/WrittenEvidence/167697/Document/OriginalFormat"
    assert first.request_hints["internal_reference"] == "BoEMPR0014"
    assert first.request_hints["business_title"] == "Bank of England Monetary Policy Reports"
    assert first.request_hints["witnesses"] == ["UK Finance", "Jane Example"]
    assert first.request_hints["page_url"] == (
        "https://committees.parliament.uk/writtenevidence/167697/"
    )


async def test_cursor_high_water_narrows_the_listing_window(
    committees_api: respx.MockRouter,
) -> None:
    cursor = Cursor(
        source_key="committee_evidence",
        state={"newest_publication_date": {"158": "2026-06-01T00:00:00"}},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    await discovered(cursor)
    called = [str(call.request.url) for call in committees_api.calls]
    assert all("StartDate=2026-06-01" in url for url in called)


async def test_missing_cursor_falls_back_to_the_options_window(
    committees_api: respx.MockRouter,
) -> None:
    await discovered()
    called = [str(call.request.url) for call in committees_api.calls]
    assert all("StartDate=2025-01-01" in url for url in called)
