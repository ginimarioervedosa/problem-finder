"""The Source protocol: everything the pipeline needs to know about a source.

Adapters implement four pure-ish stages (discover, fetch, parse, normalise)
plus a cursor fold, and declare a compliance policy. They never touch storage,
scheduling, retries, or dedupe; the ingestion layer owns all of that, driven by
the declarations here.
"""

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import ClassVar, Protocol, runtime_checkable

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, JsonValue

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal, VerbatimSignal
from problemfinder.domain.source_policy import SourcePolicy


class SourceParseError(ValueError):
    """A payload could not be interpreted. The only exception parse may raise:
    anything else escaping an adapter's parse stage is a bug, not bad data."""


class WorkItem(BaseModel):
    """One fetchable unit an adapter has discovered: a file, a page, an API call.

    `request_hints` carries discovery context the later stages need (a period,
    a page URL, a publication date); parse folds them into its records, keeping
    every stage a pure function of its inputs.
    """

    model_config = ConfigDict(frozen=True)

    external_id: str
    url: HttpUrl
    request_hints: dict[str, JsonValue] = Field(default_factory=dict)


class RawDocument(BaseModel):
    """Exactly what came over the wire, before any interpretation."""

    model_config = ConfigDict(frozen=True)

    work_item: WorkItem
    content: bytes
    media_type: str
    fetched_at: AwareDatetime
    http_status: int | None = None


class ParsedRecord(BaseModel):
    """One source-shaped record, still in the source's own vocabulary."""

    model_config = ConfigDict(frozen=True)

    external_id: str
    fields: dict[str, JsonValue] = Field(default_factory=dict)


@runtime_checkable
class Source(Protocol):
    """Implemented once per data source; registered in sources.registry."""

    key: ClassVar[str]
    version: ClassVar[int]
    policy: ClassVar[SourcePolicy]

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        """Yield fetchable units newer than the cursor. Idempotent, no side effects."""
        ...

    async def fetch(self, item: WorkItem) -> RawDocument:
        """Retrieve one unit, nothing more. The pipeline archives the result
        immutably before parse is ever called. Browser-backed sources hide the
        browser entirely inside this method."""
        ...

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        """Pure function of the raw document; no I/O. One bulk file may yield
        thousands of records."""
        ...

    def normalise(
        self, record: ParsedRecord, provenance: Provenance
    ) -> VerbatimSignal | AggregateSignal:
        """Map the source's vocabulary onto the shared schema. Pure, no I/O.
        Anything that doesn't generalise goes into extras, never dropped.
        Provenance is computed and passed in by the pipeline."""
        ...

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        """Fold successfully processed items into the next resume point."""
        ...
