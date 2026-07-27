"""The FCA complaints returns adapter: policy and the four pipeline stages."""

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
from problemfinder.sources.adapters.fca_complaints_returns.discover import (
    STATE_KEY,
    discover_releases,
)
from problemfinder.sources.adapters.fca_complaints_returns.normalise import to_signal
from problemfinder.sources.adapters.fca_complaints_returns.parser import parse_workbook
from problemfinder.sources.cursor_state import fold_ingested_keys
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.http import IDENTIFYING_USER_AGENT
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register

_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@register
class FcaComplaintsReturnsSource:
    key: ClassVar[str] = "fca_complaints_returns"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = SourcePolicy(
        method=IngestionMethod.BULK_DOWNLOAD,
        robots_status=RobotsStatus.ALLOWED,
        terms_reviewed=date(2026, 7, 27),
        terms_notes=(
            "Reviewed 2026-07-26 (fca.org.uk/legal, last updated 30/07/2025, and "
            "robots.txt): robots disallows only query-string URLs and CMS "
            "directories; the data pages and workbook paths are allowed. Legal "
            "terms clause 2.2 places numerical datasets in the Data section "
            "under the UK Open Government Licence, which grants copying and "
            "distribution; the firm-level complaints workbooks are such "
            "datasets. Clause 4.8(iii) read literally forbids any automated "
            "access without written consent; the purposive reading is that a "
            "twice-yearly scripted download of OGL-licensed open data with an "
            "identifying user agent is the intended use. The residual "
            "literal-reading risk was reviewed and accepted by the owner on "
            "2026-07-27, following the fos_decisions precedent. Full record in "
            "docs/compliance/phase-6-verdicts.md."
        ),
        rate_limit=RateLimit(requests=1, per_seconds=2.0),
        user_agent=IDENTIFYING_USER_AGENT,
    )

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_releases(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, default_media_type=_XLSX)

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_workbook(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_ingested_keys(self.key, cursor, STATE_KEY, done)
