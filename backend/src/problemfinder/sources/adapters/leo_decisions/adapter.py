"""The Legal Ombudsman decisions adapter: policy and the four stages."""

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
from problemfinder.sources.adapters.leo_decisions.discover import (
    STATE_KEY,
    discover_decision_files,
)
from problemfinder.sources.adapters.leo_decisions.normalise import to_signal
from problemfinder.sources.adapters.leo_decisions.parser import parse_decision_data
from problemfinder.sources.cursor_state import fold_ingested_keys
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.http import IDENTIFYING_USER_AGENT
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register

_CSV = "text/csv"


@register
class LeoDecisionsSource:
    key: ClassVar[str] = "leo_decisions"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = SourcePolicy(
        method=IngestionMethod.BULK_DOWNLOAD,
        robots_status=RobotsStatus.ALLOWED,
        terms_reviewed=date(2026, 7, 26),
        terms_notes=(
            "Reviewed 2026-07-26: legalombudsman.org.uk/robots.txt disallows "
            "only CMS-internal paths (/umbraco/, /bin/, /config/, /temp/). The "
            "site publishes no terms-of-use or copyright page (privacy and "
            "accessibility policies only, checked via the sitemap), so no "
            "terms restrict collection. The ombudsman-decision-data page "
            "offers the CSV explicitly as a downloadable file; decisions data "
            "is published under the scheme's statutory transparency policy."
        ),
        rate_limit=RateLimit(requests=1, per_seconds=2.0),
        user_agent=IDENTIFYING_USER_AGENT,
    )

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_decision_files(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, _CSV)

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_decision_data(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_ingested_keys(self.key, cursor, STATE_KEY, done)
