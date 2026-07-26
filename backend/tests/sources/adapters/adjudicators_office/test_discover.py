"""Discovery: search-API listing, per-publication document resolution, hints."""

from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.adapters.adjudicators_office.adapter import AdjudicatorsOfficeSource
from problemfinder.sources.adapters.adjudicators_office.discover import (
    BASE,
    SEARCH_URL,
    discover_reports,
)
from problemfinder.sources.protocol import WorkItem

POLICY = AdjudicatorsOfficeSource.policy


async def discovered(cursor: Cursor | None = None) -> list[WorkItem]:
    return [item async for item in discover_reports("adjudicators_office", POLICY, cursor)]


SEARCH_JSON = {
    "results": [
        {
            "title": "The Adjudicator's Office annual report 2026",
            "link": "/government/publications/the-adjudicators-office-annual-report-2026",
        },
        {
            "title": "The Adjudicator's Office annual report 2025",
            "link": "/government/publications/the-adjudicators-office-annual-report-2025",
        },
        {
            "title": "The Adjudicator's Office annual report 2019",
            "link": "/government/publications/the-adjudicators-office-annual-report-2019",
        },
        {
            "title": "Business plan for 2024 - 2027",
            "link": "/government/publications/business-plan-for-2024-2027",
        },
    ]
}

# The oldest reports live in the National Archives web archive, an absolute
# URL with no content-API document behind it; discovery must skip them.
PUBLICATION_2019 = {
    "first_published_at": "2019-06-25T09:30:00+01:00",
    "details": {
        "attachments": [
            {
                "title": "The Adjudicator's Office annual report 2019",
                "content_type": None,
                "url": (
                    "https://webarchive.nationalarchives.gov.uk/20200630172919/https://"
                    "www.gov.uk/government/publications/the-adjudicators-office-annual-report-2019"
                ),
            }
        ]
    },
}

# The 2026 publication's report document is slugged 2025 on the real site;
# the fixture keeps that quirk so discovery is proven not to guess from years.
PUBLICATION_2026 = {
    "first_published_at": "2026-07-13T17:19:41+01:00",
    "details": {
        "attachments": [
            {
                "title": "The Adjudicator's Office annual report 2026",
                "content_type": None,
                "url": (
                    "/government/publications/the-adjudicators-office-annual-report-2026"
                    "/the-adjudicators-office-annual-report-2025"
                ),
            },
            {
                "title": "Annual Report Data 2026",
                "content_type": "application/vnd.oasis.opendocument.spreadsheet",
                "url": "https://assets.publishing.service.gov.uk/media/x/data.ods",
            },
        ]
    },
}


@pytest.fixture
def gov_uk() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(SEARCH_URL).mock(return_value=httpx.Response(200, json=SEARCH_JSON))
        router.get(
            f"{BASE}/api/content/government/publications/the-adjudicators-office-annual-report-2026"
        ).mock(return_value=httpx.Response(200, json=PUBLICATION_2026))
        router.get(
            f"{BASE}/api/content/government/publications/the-adjudicators-office-annual-report-2025"
        ).mock(return_value=httpx.Response(404))
        router.get(
            f"{BASE}/api/content/government/publications/the-adjudicators-office-annual-report-2019"
        ).mock(return_value=httpx.Response(200, json=PUBLICATION_2019))
        yield router


async def test_resolves_each_annual_report_to_its_html_document(
    gov_uk: respx.MockRouter,
) -> None:
    # 404 publications and web-archive-only reports are skipped; the
    # business plan is never an annual report.
    [item] = await discovered()
    assert item.external_id == "annual-report-2026"
    assert str(item.url) == (
        f"{BASE}/api/content/government/publications"
        "/the-adjudicators-office-annual-report-2026/the-adjudicators-office-annual-report-2025"
    )


async def test_work_items_carry_publication_hints(gov_uk: respx.MockRouter) -> None:
    [item] = await discovered()

    assert item.request_hints["year"] == 2026
    assert item.request_hints["published_at"] == "2026-07-13T17:19:41+01:00"
    assert item.request_hints["page_url"] == (
        f"{BASE}/government/publications/the-adjudicators-office-annual-report-2026"
        "/the-adjudicators-office-annual-report-2025"
    )


async def test_reports_already_in_the_cursor_are_not_refetched(
    gov_uk: respx.MockRouter,
) -> None:
    cursor = Cursor(
        source_key="adjudicators_office",
        state={"ingested_reports": ["annual-report-2026"]},
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    assert await discovered(cursor) == []
    called = {str(call.request.url) for call in gov_uk.calls}
    assert not any("annual-report-2026" in url for url in called)
