"""Pipeline stages for the Reddit source; the policy lives in policy.py."""

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import ClassVar

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.adapters.reddit.auth import bearer_token
from problemfinder.sources.adapters.reddit.discover import discover_posts
from problemfinder.sources.adapters.reddit.normalise import to_signal
from problemfinder.sources.adapters.reddit.parser import parse_listing
from problemfinder.sources.adapters.reddit.policy import REDDIT_POLICY
from problemfinder.sources.cursor_state import fold_newest_by_group
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register


@register
class RedditSource:
    key: ClassVar[str] = "reddit"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = REDDIT_POLICY

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_posts(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        token = await bearer_token(self.key, self.policy)
        return await fetch_one(
            self.key,
            self.policy,
            item,
            default_media_type="application/json",
            headers={"Authorization": f"bearer {token}"},
        )

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_newest_by_group(
            self.key, cursor, "newest_created_utc", done, ("subreddit", "newest_created_utc")
        )

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_listing(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        return to_signal(self.key, record, provenance)
