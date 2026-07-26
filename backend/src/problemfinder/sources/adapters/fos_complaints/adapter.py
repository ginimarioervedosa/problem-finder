"""The FOS complaints adapter: policy declaration and the four pipeline stages."""

from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import date
from typing import ClassVar

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
from problemfinder.sources.cursor_state import fold_ingested_keys, ingested_keys
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.http import IDENTIFYING_USER_AGENT, client_for
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_STATE_KEY = "ingested_periods"


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
        user_agent=IDENTIFYING_USER_AGENT,
    )

    async def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        seen = ingested_keys(cursor, _STATE_KEY)
        async with client_for(self.key, self.policy) as client:
            for item in await discover_releases(client):
                if item.external_id not in seen:
                    yield item

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, default_media_type=_XLSX)

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_workbook(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_ingested_keys(self.key, cursor, _STATE_KEY, done)
