"""The FOS complaints adapter: policy declaration and the four pipeline stages."""

from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import UTC, date, datetime
from typing import ClassVar

from pydantic import JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal
from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)
from problemfinder.sources.adapters.fos_complaints.discover import discover_releases
from problemfinder.sources.adapters.fos_complaints.normalise import to_signal
from problemfinder.sources.adapters.fos_complaints.parser import parse_workbook
from problemfinder.sources.http import client_for
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@register
class FosComplaintsSource:
    key: ClassVar[str] = "fos_complaints"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = SourcePolicy(
        method=IngestionMethod.BULK_DOWNLOAD,
        robots_status=RobotsStatus.ALLOWED,
        terms_reviewed=date(2026, 7, 25),
        terms_notes=(
            "financial-ombudsman.org.uk/legal-policy permits downloading extracts for "
            "personal use; this is a single-user local research tool. robots.txt "
            "disallows only four PDF complaint forms. No API exists; the data pages "
            "publish XLSX/CSV downloads explicitly."
        ),
        rate_limit=RateLimit(requests=1, per_seconds=2.0),
        user_agent=(
            "problem-finder/0.1 (single-user research tool; contact: mario.ervedosa@thegini.co.uk)"
        ),
    )

    async def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        async with client_for(self.key, self.policy) as client:
            for item in await discover_releases(client):
                yield item

    async def fetch(self, item: WorkItem) -> RawDocument:
        async with client_for(self.key, self.policy) as client:
            response = await client.get(str(item.url))
            response.raise_for_status()
            return RawDocument(
                work_item=item,
                content=response.content,
                media_type=response.headers.get("content-type", _XLSX),
                fetched_at=datetime.now(tz=UTC),
                http_status=response.status_code,
            )

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_workbook(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        periods: list[JsonValue] = [item.external_id for item in done]
        periods.sort(key=str)
        return Cursor(
            source_key=self.key,
            state={"ingested_periods": periods},
            updated_at=datetime.now(tz=UTC),
        )
