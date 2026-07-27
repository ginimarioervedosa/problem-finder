"""The Adjudicator's Office adapter: policy declaration and the four stages."""

from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import date
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
from problemfinder.sources.adapters.adjudicators_office.discover import (
    STATE_KEY,
    discover_reports,
)
from problemfinder.sources.adapters.adjudicators_office.normalise import to_signal
from problemfinder.sources.adapters.adjudicators_office.parser import parse_report
from problemfinder.sources.cursor_state import fold_ingested_keys
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.http import IDENTIFYING_USER_AGENT
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register

_JSON = "application/json"


@register
class AdjudicatorsOfficeSource:
    key: ClassVar[str] = "adjudicators_office"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = SourcePolicy(
        method=IngestionMethod.OFFICIAL_API,
        robots_status=RobotsStatus.ALLOWED,
        terms_reviewed=date(2026, 7, 26),
        terms_notes=(
            "Reviewed 2026-07-26: www.gov.uk/robots.txt disallows only print "
            "views and site-search paths; the documented public content and "
            "search APIs (/api/content, /api/search.json) are unrestricted. "
            "gov.uk content is Crown copyright under the Open Government "
            "Licence v3.0 except where stated (site footer on every page), "
            "which grants copying, publishing and adaptation with attribution; "
            "the annual report pages carry no contrary statement."
        ),
        rate_limit=RateLimit(requests=1, per_seconds=2.0),
        user_agent=IDENTIFYING_USER_AGENT,
    )

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_reports(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, _JSON)

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_report(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_ingested_keys(self.key, cursor, STATE_KEY, done)
