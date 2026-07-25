"""One-URL fetch through the policy-configured client, shared by adapters.

Most sources fetch a work item the same way: one GET, fail loudly on a bad
status, wrap the bytes with their wire metadata. Adapters delegate here so
the behaviour lives once; a source needing more (a browser, an API envelope)
implements its own fetch instead.
"""

from collections.abc import Mapping
from datetime import UTC, datetime

from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import RawDocument, WorkItem


async def fetch_one(
    source_key: str,
    policy: SourcePolicy,
    item: WorkItem,
    default_media_type: str,
    headers: Mapping[str, str] | None = None,
) -> RawDocument:
    async with client_for(source_key, policy) as client:
        response = await client.get(str(item.url), headers=dict(headers or {}))
        response.raise_for_status()
        return RawDocument(
            work_item=item,
            content=response.content,
            media_type=response.headers.get("content-type", default_media_type),
            fetched_at=datetime.now(tz=UTC),
            http_status=response.status_code,
        )
