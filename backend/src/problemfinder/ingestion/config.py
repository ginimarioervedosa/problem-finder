"""Reads config/sources.toml: the one config entry each source ships."""

import tomllib

from problemfinder.settings import get_settings


def enabled_sources() -> set[str]:
    with get_settings().sources_config.open("rb") as handle:
        parsed = tomllib.load(handle)
    sources: dict[str, dict[str, object]] = parsed.get("sources", {})
    return {key for key, entry in sources.items() if entry.get("enabled", False)}


def is_enabled(source_key: str) -> bool:
    return source_key in enabled_sources()
