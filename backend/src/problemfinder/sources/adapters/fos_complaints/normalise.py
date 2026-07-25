"""ParsedRecord -> AggregateSignal: the FOS vocabulary mapped onto ours."""

from datetime import date, datetime

from pydantic import JsonValue

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal
from problemfinder.sources.protocol import ParsedRecord

_NO_GROUP = "No Group"


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
    fields = record.fields
    business = _text(fields, "business_name") or "Unknown business"
    category = _text(fields, "category") or "Uncategorised"
    volume = _int(fields, "volume") or 0
    upheld_share = _float(fields, "upheld_share")
    label = _period_label(_text(fields, "period") or record.external_id)
    group = _text(fields, "business_group")

    body = (
        f"{business} received {volume} new {category} complaints "
        f"at the Financial Ombudsman Service in {label}."
    )
    if upheld_share is not None:
        body += (
            f" {upheld_share:.0%} of its resolved complaints in this category "
            "were upheld in favour of the consumer."
        )

    published = _text(fields, "published_at")
    return AggregateSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=_text(fields, "page_url") or "https://www.financial-ombudsman.org.uk",
        published_at=datetime.fromisoformat(published) if published else None,
        retrieved_at=provenance.fetched_at,
        title=f"{business}: {category} complaints, {label}",
        body=body,
        firm_name=business,
        category=category,
        extras={
            "business_group": None if group == _NO_GROUP else group,
            "total_new_cases": _int(fields, "total_new_cases"),
            "period": _text(fields, "period"),
        },
        period_start=date.fromisoformat(_text(fields, "period_start") or ""),
        period_end=date.fromisoformat(_text(fields, "period_end") or ""),
        volume=volume,
        upheld_share=upheld_share,
        provenance=provenance,
    )


def _period_label(period: str) -> str:
    half, _, year = period.partition("-")
    return f"{half.upper()} {year}" if year else period


def _text(fields: dict[str, JsonValue], key: str) -> str | None:
    value = fields.get(key)
    return value if isinstance(value, str) and value else None


def _int(fields: dict[str, JsonValue], key: str) -> int | None:
    value = fields.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _float(fields: dict[str, JsonValue], key: str) -> float | None:
    value = fields.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
