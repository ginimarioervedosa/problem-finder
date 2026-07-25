"""ParsedRecord -> AggregateSignal: the FOS vocabulary mapped onto ours."""

from datetime import date, datetime

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import float_field, int_field, text_field

_NO_GROUP = "No Group"

# The GI category label drifted across eras; one canonical label keeps the
# dimension clean while extras retain the source's own wording.
_CATEGORY_CANON = {
    "general insurance / pure protection (includes ppi)": "General Insurance / Pure Protection",
    "general insurance / pure protection (including ppi)": "General Insurance / Pure Protection",
}


def canonical_category(label: str) -> str:
    return _CATEGORY_CANON.get(label.strip().casefold(), label.strip())


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
    fields = record.fields
    business = text_field(fields, "business_name") or "Unknown business"
    source_category = text_field(fields, "category") or "Uncategorised"
    category = canonical_category(source_category)
    volume = int_field(fields, "volume") or 0
    upheld_share = float_field(fields, "upheld_share")
    label = _period_label(text_field(fields, "period") or record.external_id)
    group = text_field(fields, "business_group")

    body = (
        f"{business} received {volume} new {category} complaints "
        f"at the Financial Ombudsman Service in {label}."
    )
    if upheld_share is not None:
        body += (
            f" {upheld_share:.0%} of its resolved complaints in this category "
            "were upheld in favour of the consumer."
        )

    published = text_field(fields, "published_at")
    return AggregateSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "page_url") or "https://www.financial-ombudsman.org.uk",
        published_at=datetime.fromisoformat(published) if published else None,
        retrieved_at=provenance.fetched_at,
        title=f"{business}: {category} complaints, {label}",
        body=body,
        firm_name=business,
        category=category,
        extras={
            "business_group": None if group == _NO_GROUP else group,
            "total_new_cases": int_field(fields, "total_new_cases"),
            "period": text_field(fields, "period"),
            "source_category": source_category,
        },
        period_start=date.fromisoformat(text_field(fields, "period_start") or ""),
        period_end=date.fromisoformat(text_field(fields, "period_end") or ""),
        volume=volume,
        upheld_share=upheld_share,
        provenance=provenance,
    )


def _period_label(period: str) -> str:
    half, _, year = period.partition("-")
    return f"{half.upper()} {year}" if year else period
