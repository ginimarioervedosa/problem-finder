"""Per-row reporting periods: firms report on their own half-year clocks.

A release's rows mix reporting periods (a firm whose half-year ends in
September sits in the H2 file with an April-to-September period), written as
'2025-07-01 to 2025-12-31' in recent releases and '01 July 2019 to
31 December 2019' in older ones. Unparseable text degrades to no bounds and
the release's own half-year applies downstream.
"""

import re
from datetime import datetime

from pydantic import JsonValue

_ISO_RANGE = re.compile(r"(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})")
_PROSE_RANGE = re.compile(r"(\d{1,2} \w+ \d{4})\s+to\s+(\d{1,2} \w+ \d{4})")


def row_period_bounds(reporting_period: str | None) -> dict[str, JsonValue]:
    """{'row_period_start': iso, 'row_period_end': iso} or empty when unreadable."""
    if reporting_period is None:
        return {}
    if match := _ISO_RANGE.search(reporting_period):
        return {"row_period_start": match[1], "row_period_end": match[2]}
    if match := _PROSE_RANGE.search(reporting_period):
        try:
            start, end = (datetime.strptime(text, "%d %B %Y") for text in match.groups())
        except ValueError:
            return {}
        return {
            "row_period_start": start.date().isoformat(),
            "row_period_end": end.date().isoformat(),
        }
    return {}
