"""Slugs for external-id segments, shared by every adapter that mints
`<period>:<firm-slug>:<category-slug>` style ids. One implementation so the
same label always produces the same id segment across sources."""

import re


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
