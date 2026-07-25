"""Decision PDF bytes -> one record: the write-up text plus listing hints."""

import io
import re
from collections.abc import Iterator

from pydantic import JsonValue
from pypdf import PdfReader

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_DRN_RE = re.compile(r"DRN-\d+")
_OMBUDSMAN_RE = re.compile(r"([A-Z][\w'.-]*(?: [A-Z][\w'.-]*)+)\s*\n\s*Ombudsman\s*$")
_HINT_KEYS = ("decision_date", "business", "outcome", "sector", "page_url")


def parse_decision(raw: RawDocument) -> Iterator[ParsedRecord]:
    text = _decision_text(raw.content)
    drn = _DRN_RE.search(text)
    if drn is None:
        raise SourceParseError("no decision reference (DRN) in the PDF text")
    hints = raw.work_item.request_hints
    fields: dict[str, JsonValue] = {
        "text": text,
        "drn": drn[0],
        "ombudsman": _ombudsman(text),
        "pdf_url": str(raw.work_item.url),
        **{key: hints.get(key) for key in _HINT_KEYS},
    }
    yield ParsedRecord(external_id=raw.work_item.external_id, fields=fields)


def _decision_text(content: bytes) -> str:
    # pypdf raises a menagerie of exception types on malformed input, and the
    # parse contract allows only SourceParseError out of an adapter; anything
    # the reader throws therefore means "not a readable decision PDF".
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() for page in reader.pages)
    except Exception as exc:
        raise SourceParseError(f"not a readable decision PDF: {exc}") from exc
    if not text.strip():
        raise SourceParseError("decision PDF has no extractable text")
    return _tidy(text)


def _tidy(text: str) -> str:
    """Collapse extraction artefacts without rewording anything."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _ombudsman(text: str) -> str | None:
    match = _OMBUDSMAN_RE.search(text)
    return match[1] if match else None
