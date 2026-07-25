"""Release discovery: index scrape, forward probing, and hint extraction."""

from collections.abc import Generator

import httpx
import pytest
import respx

from problemfinder.sources.adapters.fos_complaints.discover import (
    INDEX_URL,
    RELEASE_PATH,
    discover_releases,
)

INDEX_HTML = """
<html><body>
  <a href="/data-insight/our-insight/half-yearly-complaints-data-h2-2024">H2 2024</a>
  <a href="/data-insight/our-insight/half-yearly-complaints-data-h1-2025">H1 2025</a>
</body></html>
"""

RELEASE_HTML = """
<html><body>
  <p>Date published: 29 October 2025</p>
  <a href="/files/324668/Business-complaints-data-H1-2025.xlsx">Business complaints data</a>
  <a href="/files/324667/Early-resolution-data-H1-2025.xlsx">Early resolution data</a>
</body></html>
"""


@pytest.fixture
def fos_site() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(INDEX_URL).mock(return_value=httpx.Response(200, text=INDEX_HTML))
        for period in ("h2-2024", "h1-2025"):
            router.get(f"{RELEASE_PATH}-{period}").mock(
                return_value=httpx.Response(200, text=RELEASE_HTML)
            )
        for period in ("h2-2025", "h1-2026", "h2-2026"):
            router.get(f"{RELEASE_PATH}-{period}").mock(return_value=httpx.Response(404))
        yield router


async def test_discovers_all_releases_and_probes_forward(fos_site: respx.MockRouter) -> None:
    async with httpx.AsyncClient() as client:
        items = await discover_releases(client)

    assert [item.external_id for item in items] == ["h2-2024", "h1-2025"]
    assert fos_site.get(f"{RELEASE_PATH}-h2-2025").called
    assert fos_site.get(f"{RELEASE_PATH}-h1-2026").called


async def test_work_item_carries_period_and_publication_hints(
    fos_site: respx.MockRouter,
) -> None:
    async with httpx.AsyncClient() as client:
        items = await discover_releases(client)

    latest = items[-1]
    assert str(latest.url).endswith("/files/324668/Business-complaints-data-H1-2025.xlsx")
    assert latest.request_hints["period_start"] == "2025-01-01"
    assert latest.request_hints["period_end"] == "2025-06-30"
    assert latest.request_hints["published_at"] == "2025-10-29T00:00:00+00:00"
    assert latest.request_hints["page_url"] == f"{RELEASE_PATH}-h1-2025"
