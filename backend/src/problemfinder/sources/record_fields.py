"""Typed readers over a ParsedRecord's loosely typed field mapping.

Normalise stages read source fields defensively: a missing key, a null, or a
mistyped value degrades to None rather than crashing mid-corpus. Adapters
share these readers instead of hand-rolling casts.
"""

from pydantic import JsonValue


def text_field(fields: dict[str, JsonValue], key: str) -> str | None:
    value = fields.get(key)
    return value if isinstance(value, str) and value else None


def int_field(fields: dict[str, JsonValue], key: str) -> int | None:
    value = fields.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def float_field(fields: dict[str, JsonValue], key: str) -> float | None:
    value = fields.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)
