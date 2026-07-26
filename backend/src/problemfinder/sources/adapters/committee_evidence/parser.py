"""OriginalFormat envelope -> one record: the submission's extracted text.

The API wraps each document as JSON holding base64 file data plus its
original file name. Submissions arrive as PDF, docx, or HTML; PDF text is
extracted with pypdf, docx by reading word/document.xml from the zip, HTML
with selectolax. Anything else raises SourceParseError so unsupported
formats surface in the run's error ledger rather than storing empty bodies.
"""

import base64
import io
import json
import re
import zipfile
from collections.abc import Iterator

from pydantic import JsonValue
from pypdf import PdfReader
from selectolax.parser import HTMLParser

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_HINT_KEYS = (
    "committee_id",
    "internal_reference",
    "publication_date",
    "business_title",
    "witnesses",
    "page_url",
)


def parse_evidence(raw: RawDocument) -> Iterator[ParsedRecord]:
    file_name, content = _envelope(raw.content)
    fields: dict[str, JsonValue] = {
        "text": _text(file_name, content),
        "file_name": file_name,
        **{key: raw.work_item.request_hints.get(key) for key in _HINT_KEYS},
    }
    yield ParsedRecord(external_id=raw.work_item.external_id, fields=fields)


def _envelope(content: bytes) -> tuple[str, bytes]:
    try:
        document = json.loads(content)
    except (UnicodeDecodeError, ValueError) as error:
        raise SourceParseError(f"evidence envelope is not JSON: {error}") from error
    data = document.get("data") if isinstance(document, dict) else None
    if not isinstance(data, str) or not data:
        raise SourceParseError("evidence envelope has no base64 data")
    try:
        decoded = base64.b64decode(data, validate=True)
    except ValueError as error:
        raise SourceParseError(f"evidence data is not base64: {error}") from error
    file_name = document.get("fileName")
    return (file_name if isinstance(file_name, str) else ""), decoded


def _text(file_name: str, content: bytes) -> str:
    if content.startswith(b"%PDF"):
        return _pdf_text(content)
    if content.startswith(b"PK") and file_name.lower().endswith(".docx"):
        return _docx_text(content)
    if file_name.lower().endswith((".html", ".htm")) or content.lstrip()[:1] == b"<":
        tree = HTMLParser(content.decode("utf-8", errors="replace"))
        return tree.body.text(separator="\n", strip=True) if tree.body else ""
    raise SourceParseError(f"unsupported evidence format: {file_name or 'unnamed file'}")


def _docx_text(content: bytes) -> str:
    """Paragraph text out of the docx main document part, no dependency."""
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            document = archive.read("word/document.xml").decode("utf-8", errors="replace")
    except (zipfile.BadZipFile, KeyError) as error:
        raise SourceParseError(f"unreadable evidence docx: {error}") from error
    paragraphs = []
    for paragraph in re.split(r"</w:p>", document):
        runs = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", paragraph, flags=re.S)
        if runs:
            paragraphs.append(HTMLParser("".join(runs)).text())
    return "\n".join(paragraphs)


def _pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as error:  # pypdf raises a zoo of types; all mean bad payload
        raise SourceParseError(f"unreadable evidence PDF: {error}") from error
