"""Content-API JSON bytes -> one record per case study in the report body.

Case studies sit under h2/h3 headings containing "case study" in every report
era, in varying shapes ("Case study 4: topic", "Case Study 1, Decision: Fully
Upheld", a bare "Case Study"). A record is one such heading plus everything
until the next h2/h3; plural "Case Studies" section labels are boundaries,
not records. Decision outcomes and business areas are lifted from the heading
or from a "Business Area" sub-heading where the era provides them.
"""

import json
import re
from collections.abc import Iterator

from pydantic import JsonValue
from selectolax.parser import HTMLParser

from problemfinder.sources.protocol import ParsedRecord, RawDocument, SourceParseError

_HEADING_RE = re.compile(r"^case\s+stud(?:y|ies)", re.IGNORECASE)
_LABEL_ONLY_RE = re.compile(r"^case\s+studies$", re.IGNORECASE)
_DECISION_RE = re.compile(r"decision:?\s*([a-z][a-z ]*[a-z])", re.IGNORECASE)
_AREA_RE = re.compile(r"business\s+area:?\s*(.+?)\s*\.?\s*$", re.IGNORECASE)
_HINT_KEYS = ("year", "page_url", "published_at")


def parse_report(raw: RawDocument) -> Iterator[ParsedRecord]:
    tree = HTMLParser(_report_body(raw.content))
    hints = raw.work_item.request_hints
    for ordinal, (heading, blocks) in enumerate(_case_study_segments(tree), start=1):
        yield _record(raw.work_item.external_id, ordinal, heading, blocks, hints)


def _report_body(content: bytes) -> str:
    try:
        document = json.loads(content)
    except (UnicodeDecodeError, ValueError) as error:
        raise SourceParseError(f"content API payload is not JSON: {error}") from error
    details = document.get("details") if isinstance(document, dict) else None
    body = details.get("body") if isinstance(details, dict) else None
    if not isinstance(body, str) or not body.strip():
        raise SourceParseError("content API payload has no details.body")
    return body


_BOUNDARY_TAGS = frozenset({"h2", "h3"})
_BLOCK_TAGS = frozenset({"h4", "p", "ul", "ol"})


def _case_study_segments(tree: HTMLParser) -> Iterator[tuple[str, list[str]]]:
    """(heading text, block texts) per case study, in document order.

    css() groups matches per selector, so segmentation traverses instead;
    blocks nested inside other blocks (a p within an li) are skipped because
    the outer block's deep text already carries them.
    """
    heading: str | None = None
    blocks: list[str] = []
    root = tree.body or tree.root
    if root is None:
        return
    for node in root.traverse(include_text=False):
        if node.tag in _BOUNDARY_TAGS:
            if heading is not None:
                yield heading, blocks
            text = node.text(deep=True, separator=" ", strip=True)
            is_case_study = bool(_HEADING_RE.match(text)) and not _LABEL_ONLY_RE.match(text)
            heading = text if is_case_study else None
            blocks = []
        elif heading is not None and node.tag in _BLOCK_TAGS and not _nested_block(node):
            text = node.text(deep=True, separator=" ", strip=True)
            if text:
                blocks.append(text)
    if heading is not None:
        yield heading, blocks


def _nested_block(node: object) -> bool:
    parent = getattr(node, "parent", None)
    while parent is not None:
        if parent.tag in _BLOCK_TAGS:
            return True
        parent = parent.parent
    return False


def _record(
    report: str, ordinal: int, heading: str, blocks: list[str], hints: dict[str, JsonValue]
) -> ParsedRecord:
    area: str | None = None
    texts: list[str] = []
    for block in blocks:
        matched = _AREA_RE.fullmatch(block) if len(block) <= 80 else None
        if matched and area is None:
            area = matched[1]
        else:
            texts.append(block)
    if area is None and (in_heading := _AREA_RE.search(heading)) is not None:
        area = in_heading[1]
    decision = _DECISION_RE.search(heading)
    fields: dict[str, JsonValue] = {
        "heading": heading,
        "text": "\n\n".join(texts),
        "decision": decision[1].strip() if decision else None,
        "business_area": area,
        **{key: hints.get(key) for key in _HINT_KEYS},
    }
    return ParsedRecord(external_id=f"{report}:case-study-{ordinal:02d}", fields=fields)
