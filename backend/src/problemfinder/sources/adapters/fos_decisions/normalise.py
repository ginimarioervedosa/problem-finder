"""ParsedRecord -> VerbatimSignal: one ombudsman decision in its own words."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import text_field

_FALLBACK_URL = "https://www.financial-ombudsman.org.uk/decision/{drn}.pdf"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
    fields = record.fields
    business = text_field(fields, "business")
    outcome = text_field(fields, "outcome")
    decided = text_field(fields, "decision_date")
    title = f"Ombudsman decision {record.external_id}: {business or 'unnamed business'}"
    if outcome:
        title += f" ({outcome.casefold()})"
    return VerbatimSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "pdf_url") or _FALLBACK_URL.format(drn=record.external_id),
        published_at=_midnight_utc(decided),
        retrieved_at=provenance.fetched_at,
        title=title,
        body=text_field(fields, "text") or "",
        firm_name=business,
        category=text_field(fields, "sector"),
        author_handle=None,  # decisions are anonymised at source, by design
        extras={
            "outcome": outcome,
            "ombudsman": text_field(fields, "ombudsman"),
            "page_url": text_field(fields, "page_url"),
        },
        provenance=provenance,
    )


def _midnight_utc(iso_date: str | None) -> datetime | None:
    return datetime.fromisoformat(iso_date).replace(tzinfo=UTC) if iso_date else None
