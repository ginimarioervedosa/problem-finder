"""A minimal in-memory Source used by registry and pipeline tests.

It records the order of stage calls in `events`, which is how the pipeline
tests assert invariants like archive-before-parse.
"""

from collections.abc import AsyncIterator, Iterator, Sequence
from datetime import UTC, date, datetime
from typing import ClassVar

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem

STUB_POLICY = SourcePolicy(
    method=IngestionMethod.BULK_DOWNLOAD,
    robots_status=RobotsStatus.NOT_APPLICABLE,
    terms_reviewed=date(2026, 7, 1),
    terms_notes="synthetic test source",
    rate_limit=RateLimit(requests=1000, per_seconds=1.0, burst=1000),
    user_agent="problem-finder-tests (contact: tests@example.org)",
)


class StubSource:
    key: ClassVar[str] = "stub"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = STUB_POLICY

    def __init__(self, item_ids: Sequence[str] = ("item-1",)) -> None:
        self._item_ids = list(item_ids)
        self.events: list[tuple[str, str]] = []

    async def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        for item_id in self._item_ids:
            self.events.append(("discover", item_id))
            yield WorkItem(external_id=item_id, url=f"https://example.org/{item_id}")

    async def fetch(self, item: WorkItem) -> RawDocument:
        self.events.append(("fetch", item.external_id))
        if item.external_id == "boom":
            raise RuntimeError("synthetic fetch failure")
        return RawDocument(
            work_item=item,
            content=f"payload for {item.external_id}".encode(),
            media_type="text/plain",
            fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
        )

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        self.events.append(("parse", raw.work_item.external_id))
        yield ParsedRecord(
            external_id=raw.work_item.external_id,
            fields={"text": raw.content.decode()},
        )

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        self.events.append(("normalise", record.external_id))
        return VerbatimSignal(
            id=signal_id_for(self.key, record.external_id),
            source_key=self.key,
            external_id=record.external_id,
            url=f"https://example.org/{record.external_id}",
            published_at=None,
            retrieved_at=datetime(2026, 7, 1, tzinfo=UTC),
            title=None,
            body=str(record.fields["text"]),
            provenance=provenance,
        )

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        state: dict[str, str] = {"last": done[-1].external_id} if done else {}
        return Cursor(
            source_key=self.key,
            state=dict(state),
            updated_at=datetime(2026, 7, 1, tzinfo=UTC),
        )
