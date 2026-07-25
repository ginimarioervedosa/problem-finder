"""Reads config/sources.toml: the one config entry each source ships.

Lives in the sources tier so adapters can read their own `options` table
(a date window, a subreddit list) without the core ever learning what any
option means. Enablement and schedules are read by the layers above.
"""

import tomllib
from collections.abc import Mapping

from problemfinder.settings import get_settings


def _entries() -> dict[str, dict[str, object]]:
    with get_settings().sources_config.open("rb") as handle:
        parsed = tomllib.load(handle)
    sources: dict[str, dict[str, object]] = parsed.get("sources", {})
    return sources


def enabled_sources() -> set[str]:
    return {key for key, entry in _entries().items() if entry.get("enabled", False)}


def is_enabled(source_key: str) -> bool:
    return source_key in enabled_sources()


def source_options(source_key: str) -> Mapping[str, object]:
    """The source's own `options` table, opaque to everything but its adapter."""
    options = _entries().get(source_key, {}).get("options", {})
    return options if isinstance(options, dict) else {}


def schedules() -> Mapping[str, str]:
    """Cron expression per enabled source that declares one; consumed by the worker."""
    return {
        key: str(entry["schedule"])
        for key, entry in _entries().items()
        if entry.get("enabled", False) and "schedule" in entry
    }
