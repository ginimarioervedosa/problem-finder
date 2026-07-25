"""Discovery: index file links, sitemap release pages, and hint extraction."""

from collections.abc import Generator

import httpx
import pytest
import respx

from problemfinder.sources.adapters.fos_complaints.discover import (
    BASE,
    INDEX_URL,
    SITEMAP_URL,
    discover_releases,
)

RELEASE_PATH = "/businesses/resolving-complaint/our-insight/half-yearly-complaints-data"

INDEX_HTML = """
<html><head><base href="https://www.financial-ombudsman.org.uk/"></head><body>
  <a href="files/289189/Business-complaints-data-H1-2019.xlsx">H1 2019 data</a>
  <a href="files/295942/Business-complaints-data-H2-2020.xlsx">H2 2020 data</a>
</body></html>
"""

# The real sitemap sometimes carries a malformed host; only the path is trusted.
SITEMAP_XML = f"""
<urlset>
  <url><loc>https://www.financial-ombudsman.org.u{RELEASE_PATH}-h1-2025</loc></url>
  <url><loc>https://www.financial-ombudsman.org.uk{RELEASE_PATH}-h2-2024</loc></url>
  <url><loc>https://www.financial-ombudsman.org.uk/some/other/page</loc></url>
</urlset>
"""

# Real release pages link files relative with no leading slash, resolved by a <base> tag.
RELEASE_HTML = """
<html><head><base href="https://www.financial-ombudsman.org.uk/"></head><body>
  <p>Date published: 29 October 2025</p>
  <a href="files/324668/Business-complaints-data-H1-2025.xlsx">Business complaints data</a>
  <a href="files/324667/Early-resolution-data-H1-2025.xlsx">Early resolution data</a>
</body></html>
"""


@pytest.fixture
def fos_site() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(INDEX_URL).mock(return_value=httpx.Response(200, text=INDEX_HTML))
        router.get(SITEMAP_URL).mock(return_value=httpx.Response(200, text=SITEMAP_XML))
        router.get(f"{BASE}{RELEASE_PATH}-h1-2025").mock(
            return_value=httpx.Response(200, text=RELEASE_HTML)
        )
        router.get(f"{BASE}{RELEASE_PATH}-h2-2024").mock(return_value=httpx.Response(404))
        yield router


async def test_combines_index_files_with_sitemap_release_pages(
    fos_site: respx.MockRouter,
) -> None:
    async with httpx.AsyncClient() as client:
        items = await discover_releases(client)

    assert [item.external_id for item in items] == ["h1-2019", "h2-2020", "h1-2025"]
    called = {str(call.request.url) for call in fos_site.calls}
    assert f"{BASE}{RELEASE_PATH}-h2-2024" in called  # 404 pages are skipped, not fatal


async def test_index_items_resolve_against_the_base_tag(fos_site: respx.MockRouter) -> None:
    async with httpx.AsyncClient() as client:
        items = await discover_releases(client)

    h1_2019 = items[0]
    assert (
        str(h1_2019.url)
        == "https://www.financial-ombudsman.org.uk/files/289189/Business-complaints-data-H1-2019.xlsx"
    )
    assert h1_2019.request_hints["period_start"] == "2019-01-01"
    assert h1_2019.request_hints["published_at"] is None


async def test_release_page_items_carry_publication_hints(fos_site: respx.MockRouter) -> None:
    async with httpx.AsyncClient() as client:
        items = await discover_releases(client)

    latest = items[-1]
    assert str(latest.url).endswith("/files/324668/Business-complaints-data-H1-2025.xlsx")
    assert latest.request_hints["published_at"] == "2025-10-29T00:00:00+00:00"
    assert latest.request_hints["page_url"] == f"{BASE}{RELEASE_PATH}-h1-2025"
