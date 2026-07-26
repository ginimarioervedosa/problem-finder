"""ParsedRecord -> VerbatimSignal: one written-evidence submission."""

from datetime import UTC, datetime

from pydantic import JsonValue

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import int_field, text_field

_FALLBACK_URL = "https://committees.parliament.uk"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
    fields = record.fields
    reference = text_field(fields, "internal_reference") or record.external_id
    business = text_field(fields, "business_title")
    witnesses = _witness_names(fields.get("witnesses"))
    title = f"Written evidence {reference}"
    if business:
        title += f": {business}"
    return VerbatimSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "page_url") or _FALLBACK_URL,
        published_at=_aware(text_field(fields, "publication_date")),
        retrieved_at=provenance.fetched_at,
        title=title,
        body=text_field(fields, "text") or "",
        firm_name=witnesses[0] if witnesses else None,
        category=business,
        author_handle="; ".join(witnesses) if witnesses else None,
        extras={
            "internal_reference": reference,
            "committee_id": int_field(fields, "committee_id"),
            "file_name": text_field(fields, "file_name"),
        },
        provenance=provenance,
    )


def _witness_names(value: JsonValue | None) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(name) for name in value if isinstance(name, str) and name]


def _aware(iso_datetime: str | None) -> datetime | None:
    """The API emits naive timestamps; they are treated as UTC."""
    if iso_datetime is None:
        return None
    try:
        parsed = datetime.fromisoformat(iso_datetime)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
