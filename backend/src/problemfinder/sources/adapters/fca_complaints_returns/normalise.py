"""ParsedRecord -> AggregateSignal: the FCA's return vocabulary onto ours."""

from datetime import date

from pydantic import JsonValue

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import float_field, int_field, text_field

_NO_GROUP = "NO GROUP"
_FALLBACK_URL = "https://www.fca.org.uk/data/complaints-data"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
    fields = record.fields
    firm = text_field(fields, "firm_name") or "Unknown firm"
    category = text_field(fields, "category") or "Uncategorised"
    volume = int_field(fields, "volume") or 0
    upheld_share = float_field(fields, "upheld_share")
    closed = int_field(fields, "closed")
    label = _period_label(text_field(fields, "period") or record.external_id)
    group = text_field(fields, "firm_group")

    body = (
        f"{firm} reported {volume} {category} complaints opened "
        f"in its FCA complaints return for {label}."
    )
    if upheld_share is not None:
        body += f" It upheld {upheld_share:.0%} of the complaints it closed in this product group."

    return AggregateSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "page_url") or _FALLBACK_URL,
        published_at=None,  # the release pages state no publication timestamp
        retrieved_at=provenance.fetched_at,
        title=f"{firm}: {category} complaints return, {label}",
        body=body,
        firm_name=firm,
        category=category,
        extras={
            "firm_group": None if group == _NO_GROUP else group,
            "joint_reporting": text_field(fields, "joint_reporting"),
            "reporting_period": text_field(fields, "reporting_period"),
            "closed": closed,
        },
        period_start=_bound(fields, "row_period_start", "period_start"),
        period_end=_bound(fields, "row_period_end", "period_end"),
        volume=volume,
        upheld_share=upheld_share,
        denominator=closed,
        provenance=provenance,
    )


def _bound(fields: dict[str, JsonValue], row_key: str, release_key: str) -> date:
    value = fields.get(row_key) or fields.get(release_key)
    return date.fromisoformat(str(value))


def _period_label(period: str) -> str:
    half, _, year = period.partition("-")
    return f"{half.upper()} {year}" if year else period
