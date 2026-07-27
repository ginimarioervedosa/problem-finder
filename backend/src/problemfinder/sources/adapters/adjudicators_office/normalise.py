"""ParsedRecord -> VerbatimSignal: one case study in the Adjudicator's words."""

from datetime import UTC, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import VerbatimSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import int_field, text_field

_FALLBACK_URL = "https://www.gov.uk/government/organisations/the-adjudicator-s-office"

# Case studies name the department they concern in the narrative; first
# mention wins. Keys are match substrings, values the canonical firm name.
_DEPARTMENTS = (
    ("HMRC", "HMRC"),
    ("Home Office", "Home Office"),
    ("Valuation Office", "Valuation Office Agency"),
)


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> VerbatimSignal:
    fields = record.fields
    body = text_field(fields, "text") or ""
    return VerbatimSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "page_url") or _FALLBACK_URL,
        published_at=_aware(text_field(fields, "published_at")),
        retrieved_at=provenance.fetched_at,
        title=text_field(fields, "heading"),
        body=body,
        firm_name=_department(body),
        category=text_field(fields, "business_area"),
        author_handle=None,  # case studies are anonymised at source, by design
        extras={
            "outcome": text_field(fields, "decision"),
            "report_year": int_field(fields, "year"),
        },
        provenance=provenance,
    )


def _department(body: str) -> str | None:
    positions = [
        (position, name) for match, name in _DEPARTMENTS if (position := body.find(match)) >= 0
    ]
    return min(positions)[1] if positions else None


def _aware(iso_datetime: str | None) -> datetime | None:
    if iso_datetime is None:
        return None
    parsed = datetime.fromisoformat(iso_datetime)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
