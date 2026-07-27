"""Pipeline stages for committee evidence; the policy lives in policy.py."""

from collections.abc import AsyncIterator, Iterator, Sequence
from typing import ClassVar

from problemfinder.domain.cursor import Cursor
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.adapters.committee_evidence.discover import discover_evidence
from problemfinder.sources.adapters.committee_evidence.normalise import to_signal
from problemfinder.sources.adapters.committee_evidence.parser import parse_evidence
from problemfinder.sources.adapters.committee_evidence.policy import COMMITTEE_EVIDENCE_POLICY
from problemfinder.sources.cursor_state import fold_newest_by_group
from problemfinder.sources.fetch import fetch_one
from problemfinder.sources.protocol import ParsedRecord, RawDocument, WorkItem
from problemfinder.sources.registry import register


@register
class CommitteeEvidenceSource:
    key: ClassVar[str] = "committee_evidence"
    version: ClassVar[int] = 1
    policy: ClassVar[SourcePolicy] = COMMITTEE_EVIDENCE_POLICY

    def discover(self, cursor: Cursor | None) -> AsyncIterator[WorkItem]:
        return discover_evidence(self.key, self.policy, cursor)

    async def fetch(self, item: WorkItem) -> RawDocument:
        return await fetch_one(self.key, self.policy, item, default_media_type="application/json")

    def cursor_after(self, cursor: Cursor | None, done: Sequence[WorkItem]) -> Cursor:
        return fold_newest_by_group(
            self.key, cursor, "newest_publication_date", done, ("committee_id", "publication_date")
        )

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        return parse_evidence(raw)

    def normalise(self, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
        return to_signal(self.key, record, provenance)
