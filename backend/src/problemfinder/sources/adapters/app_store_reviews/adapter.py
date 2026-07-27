"""Pipeline stages for App Store reviews; the policy lives in policy.py."""

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import ClassVar

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.adapters.app_store_reviews.discover import (
    STATE_KEY,
    discover_review_pages,
)
from problemfinder.sources.adapters.app_store_reviews.normalise import to_signal
from problemfinder.sources.adapters.app_store_reviews.parser import parse_review_page
from problemfinder.sources.adapters.app_store_reviews.policy import APP_STORE_REVIEWS_POLICY
from problemfinder.sources.cursor_state import fold_newest_by_group
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register


@register
class AppStoreReviewsSource:
    key: ClassVar[str] = "app_store_reviews"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = APP_STORE_REVIEWS_POLICY

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_review_pages(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, default_media_type="application/json")

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_review_page(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        return to_signal(self.key, record, provenance)

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_newest_by_group(self.key, cursor, STATE_KEY, done, ("app_id", "newest_updated"))
