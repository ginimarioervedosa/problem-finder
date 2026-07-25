"""ParsedRecord -> VerbatimSignal: one Reddit post in its author's own words."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import float_field, int_field, text_field

_BASE = "https://www.reddit.com"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
    fields = record.fields
    title = text_field(fields, "title")
    permalink = text_field(fields, "permalink")
    created = float_field(fields, "created_utc")
    return VerbatimSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=f"{_BASE}{permalink}" if permalink else f"{_BASE}/comments/{record.external_id}",
        published_at=datetime.fromtimestamp(created, tz=UTC) if created else None,
        retrieved_at=provenance.fetched_at,
        title=title,
        # Link posts have no selftext; the title is then the author's words.
        body=text_field(fields, "selftext") or title or "",
        firm_name=None,
        category=None,
        author_handle=text_field(fields, "author"),
        extras={
            "subreddit": text_field(fields, "subreddit"),
            "score": int_field(fields, "score"),
            "num_comments": int_field(fields, "num_comments"),
        },
        provenance=provenance,
    )
