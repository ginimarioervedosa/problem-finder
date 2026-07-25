"""The FOS decisions adapter: policy declaration and the four pipeline stages."""

from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import UTC, date, datetime
from typing import ClassVar

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)
from problemfinder.sources.adapters.fos_decisions.discover import discover_decisions
from problemfinder.sources.adapters.fos_decisions.normalise import to_signal
from problemfinder.sources.adapters.fos_decisions.parser import parse_decision
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.http import IDENTIFYING_USER_AGENT
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register


@register
class FosDecisionsSource:
    key: ClassVar[str] = "fos_decisions"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = SourcePolicy(
        method=IngestionMethod.BULK_DOWNLOAD,
        robots_status=RobotsStatus.ALLOWED,
        terms_reviewed=date(2026, 7, 25),
        terms_notes=(
            "Reviewed 2026-07-25: robots.txt disallows only four complaint-form "
            "PDFs; the decisions search and decision PDFs are crawlable. "
            "financial-ombudsman.org.uk/legal-policy permits downloading extracts "
            "for personal use, unmodified and not in a misleading context. "
            "Decisions are statutory publications (FSMA 2000 as amended by the "
            "Financial Services Act 2012), anonymised at source. The legal page's "
            "clause against storing site content in a public or private "
            "electronic retrieval system is read purposively as anti-"
            "republication: this tool is single-user and local, never "
            "republishes, and every signal cites its DRN and source URL. The "
            "residual literal-reading risk was reviewed and accepted by the "
            "owner on 2026-07-25."
        ),
        rate_limit=RateLimit(requests=1, per_seconds=2.0),
        user_agent=IDENTIFYING_USER_AGENT,
    )

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_decisions(self.key, self.policy)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, default_media_type="application/pdf")

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_decision(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        dates = [str(hint) for item in done if (hint := item.request_hints.get("decision_date"))]
        return Cursor(
            source_key=self.key,
            state={"latest_decision_date": max(dates, default=None)},
            updated_at=datetime.now(tz=UTC),
        )
