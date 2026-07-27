"""Discovery: the data page's CSV links become work items, once each."""

from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.adapters.leo_decisions.adapter import LeoDecisionsSource
from problemfinder.sources.adapters.leo_decisions.discover import (
    BASE,
    DATA_PAGE_URL,
    discover_decision_files,
)
from problemfinder.sources.protocol import WorkItem

POLICY = LeoDecisionsSource.policy

DATA_PAGE_HTML = """
<html><body>
  <a href="/media/ph4nn4wp/q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026.csv">
    Downloadable file</a>
  <a href="/media/ph4nn4wp/q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026.csv">
    Same file, second link</a>
  <a href="/media/f05j3veh/leo_logo.png">Logo</a>
  <a href="/information-centre/data-centre/">Data centre</a>
</body></html>
"""


async def discovered(cursor: Cursor | None = None) -> list[WorkItem]:
    return [item async for item in discover_decision_files("leo_decisions", POLICY, cursor)]


@pytest.fixture
def leo_site() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(DATA_PAGE_URL).mock(return_value=httpx.Response(200, text=DATA_PAGE_HTML))
        yield router


async def test_each_csv_becomes_one_work_item(leo_site: respx.MockRouter) -> None:
    [item] = await discovered()
    assert item.external_id == ("q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026")
    assert str(item.url) == (
        f"{BASE}/media/ph4nn4wp"
        "/q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026.csv"
    )
    assert item.request_hints["page_url"] == DATA_PAGE_URL


async def test_files_already_in_the_cursor_are_skipped(leo_site: respx.MockRouter) -> None:
    cursor = Cursor(
        source_key="leo_decisions",
        state={
            "ingested_files": ["q1-25-26-q4-25-26-web-version-final-downloadable-file-22-06-2026"]
        },
        updated_at=datetime(2026, 7, 1, tzinfo=UTC),
    )
    assert await discovered(cursor) == []
