"""CSV bytes -> one record per published ombudsman decision row.

Column headings are mapped to snake_case names here so normalise reads a
stable vocabulary; "N/A" markers on not-upheld rows degrade to None.
"""

import csv
import io
from collections.abc import Iterator

from pydantic import JsonValue

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_COLUMNS = {
    "Organisation": "organisation",
    "Organisation Type": "organisation_type",
    "Nb of Decision Required": "decisions_required",
    "Ombudsman Remedy Required": "remedy_required",
    "Area of Service Group": "area_of_law",
    "Date of Decision": "decision_date",
    "ID": "decision_id",
    "Remedy Types": "remedy_types",
    "Remedy Amount": "remedy_amount",
    "Upheld Complaint Types": "upheld_complaint_types",
    "Evidence of Poor Service": "evidence_of_poor_service",
    "Concluded Period": "concluded_period",
    "Complaint Handling Reasonable": "complaint_handling_reasonable",
}


def parse_decision_data(raw: RawDocument) -> Iterator[ParsedRecord]:
    reader = csv.DictReader(io.StringIO(_decode(raw.content)))
    header = reader.fieldnames or []
    missing = [column for column in _COLUMNS if column not in header]
    if missing:
        raise SourceParseError(f"decision data lacks expected columns: {missing}")
    page_url = raw.work_item.request_hints.get("page_url")
    for row in reader:
        decision_id = _cell(row, "ID")
        if decision_id is None:
            continue
        fields: dict[str, JsonValue] = {
            name: _cell(row, column) for column, name in _COLUMNS.items()
        }
        fields["page_url"] = page_url
        yield ParsedRecord(external_id=decision_id, fields=fields)


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise SourceParseError(f"decision data is not UTF-8 text: {error}") from error


def _cell(row: dict[str, str | None], column: str) -> str | None:
    value = (row.get(column) or "").strip()
    return value if value and value.upper() != "N/A" else None
