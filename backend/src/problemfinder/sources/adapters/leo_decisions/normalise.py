"""ParsedRecord -> AggregateSignal: one published LeO decision row."""

import re
from datetime import UTC, date, datetime

from pydantic import JsonValue

from problemfinder.domain.identity import signal_id_for
from problemfinder.domain.provenance import Provenance
from problemfinder.domain.signal import AggregateSignal
from problemfinder.sources.protocol import ParsedRecord
from problemfinder.sources.record_fields import text_field

_FALLBACK_URL = "https://www.legalombudsman.org.uk/information-centre/data-centre/"
_PERIOD_RE = re.compile(r"(\d{4})-\d{4}\s*Q\s*([1-4])")
# UK financial-year quarters: Q1 is April-June, Q4 is January-March.
_QUARTER_BOUNDS = {
    "1": ((0, 4, 1), (0, 6, 30)),
    "2": ((0, 7, 1), (0, 9, 30)),
    "3": ((0, 10, 1), (0, 12, 31)),
    "4": ((1, 1, 1), (1, 3, 31)),
}


def to_signal(source_key: str, record: ParsedRecord, provenance: Provenance) -> AggregateSignal:
    fields = record.fields
    organisation = text_field(fields, "organisation") or "Unknown organisation"
    area = text_field(fields, "area_of_law") or "Uncategorised"
    upheld = text_field(fields, "remedy_required") == "1"
    decided = _decision_date(text_field(fields, "decision_date"))
    period = _period_bounds(text_field(fields, "concluded_period"), decided)
    return AggregateSignal(
        id=signal_id_for(source_key, record.external_id),
        source_key=source_key,
        external_id=record.external_id,
        url=text_field(fields, "page_url") or _FALLBACK_URL,
        published_at=datetime.combine(decided, datetime.min.time(), tzinfo=UTC)
        if decided
        else None,
        retrieved_at=provenance.fetched_at,
        title=f"{organisation}: {area} decision {record.external_id}",
        body=_body(record.external_id, organisation, area, upheld, fields),
        firm_name=organisation,
        category=area,
        extras={
            key: text_field(fields, key)
            for key in (
                "organisation_type",
                "remedy_types",
                "remedy_amount",
                "upheld_complaint_types",
                "evidence_of_poor_service",
                "complaint_handling_reasonable",
                "concluded_period",
            )
        },
        period_start=period[0],
        period_end=period[1],
        volume=1,
        upheld_share=1.0 if upheld else 0.0,
        provenance=provenance,
    )


def _body(
    decision_id: str, organisation: str, area: str, upheld: bool, fields: dict[str, JsonValue]
) -> str:
    body = f"The Legal Ombudsman decided complaint {decision_id} about {organisation} ({area})."
    if not upheld:
        return body + " No ombudsman remedy was required."
    complaint_types = text_field(fields, "upheld_complaint_types")
    if complaint_types:
        body += f" Upheld complaint types: {complaint_types}."
    remedy = text_field(fields, "remedy_types")
    if remedy:
        amount = text_field(fields, "remedy_amount")
        body += f" Remedy directed: {remedy}" + (f" ({amount})." if amount else ".")
    return body


def _decision_date(value: str | None) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=UTC).date()
    except ValueError:
        return None


def _period_bounds(period: str | None, decided: date | None) -> tuple[date, date]:
    """The concluded quarter's bounds, falling back to the decision date."""
    match = _PERIOD_RE.search(period or "")
    if match:
        first_year = int(match[1])
        (start_offset, start_month, start_day), (end_offset, end_month, end_day) = _QUARTER_BOUNDS[
            match[2]
        ]
        return (
            date(first_year + start_offset, start_month, start_day),
            date(first_year + end_offset, end_month, end_day),
        )
    fallback = decided or date(1970, 1, 1)
    return fallback, fallback
