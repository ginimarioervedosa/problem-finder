"""Discovery: both data pages, era cutoff, slug quirks, cursor skipping."""

from collections.abc import Generator
from datetime import UTC, datetime

import httpx
import pytest
import respx

from problemfinder.domain.cursor import Cursor
from problemfinder.sources.adapters.fca_complaints_returns.discover import (
    FIRM_LEVEL_URL,
    PREVIOUS_URL,
    discover_releases,
)
from problemfinder.sources.protocol import WorkItem
from problemfinder.sources.registry import get

FIRM_LEVEL_HTML = """
<html><body>
  <a href="/publication/data/firm-level-complaints-data-2025-h2.xlsx">2025 H2</a>
  <a href="/publication/data/aggregate-complaints-data-2025-h2.xlsx">aggregate, ignored</a>
</body></html>
"""

# Real quirks: the 2016 H2 slug carries a _0 suffix, 2015 H1 is an absolute URL
# under /sites/default/files/, and 2016 H1 belongs to the pre-modern era.
PREVIOUS_HTML = """
<html><body>
  <a href="/publication/data/firm-level-complaints-data-2025-h2.xlsx">2025 H2 again</a>
  <a href="/publication/data/firm-level-complaints-data-2016-h2_0.xlsx">2016 H2</a>
  <a href="/publication/data/firm-level-complaints-data-2016-h1.xlsx">2016 H1, old era</a>
  <a href="https://www.fca.org.uk/sites/default/files/firm-level-complaints-data-2015-h1.xlsx">old</a>
</body></html>
"""


@pytest.fixture
def fca_site() -> Generator[respx.MockRouter]:
    with respx.mock(assert_all_called=False) as router:
        router.get(FIRM_LEVEL_URL).mock(return_value=httpx.Response(200, text=FIRM_LEVEL_HTML))
        router.get(PREVIOUS_URL).mock(return_value=httpx.Response(200, text=PREVIOUS_HTML))
        yield router


async def collect(cursor: Cursor | None) -> list[WorkItem]:
    source = get("fca_complaints_returns")
    return [item async for item in discover_releases(source.key, source.policy, cursor)]


async def test_combines_both_pages_and_stops_at_the_modern_era(
    fca_site: respx.MockRouter,
) -> None:
    items = await collect(None)
    assert [item.external_id for item in items] == ["h2-2016", "h2-2025"]


async def test_irregular_slugs_resolve_from_hrefs_never_construction(
    fca_site: respx.MockRouter,
) -> None:
    [h2_2016, h2_2025] = await collect(None)
    assert str(h2_2016.url).endswith("/publication/data/firm-level-complaints-data-2016-h2_0.xlsx")
    assert str(h2_2025.url) == (
        "https://www.fca.org.uk/publication/data/firm-level-complaints-data-2025-h2.xlsx"
    )
    assert h2_2016.request_hints["period_start"] == "2016-07-01"
    assert h2_2025.request_hints["page_url"] == FIRM_LEVEL_URL


async def test_ingested_periods_are_not_rediscovered(fca_site: respx.MockRouter) -> None:
    cursor = Cursor(
        source_key="fca_complaints_returns",
        state={"ingested_periods": ["h2-2016"]},
        updated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    items = await collect(cursor)
    assert [item.external_id for item in items] == ["h2-2025"]
