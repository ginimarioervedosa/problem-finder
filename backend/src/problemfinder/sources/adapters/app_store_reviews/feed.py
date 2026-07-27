"""Readers over the feed's XML-to-JSON shape, shared by discover and parse.

Every value sits under a 'label' key, and a page with one review serves
'entry' as a bare object instead of a list; both quirks are absorbed here.
"""


def feed_entries(document: object) -> list[dict[str, object]]:
    feed = document.get("feed") if isinstance(document, dict) else None
    entries = feed.get("entry") if isinstance(feed, dict) else None
    if isinstance(entries, dict):
        entries = [entries]
    return (
        [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []
    )


def label(entry: dict[str, object], key: str) -> str | None:
    value = entry.get(key)
    text = value.get("label") if isinstance(value, dict) else None
    return str(text) if text is not None and str(text) != "" else None


def author_name(entry: dict[str, object]) -> str | None:
    author = entry.get("author")
    name = author.get("name") if isinstance(author, dict) else None
    return label({"name": name} if isinstance(name, dict) else {}, "name")


def updated_at(entry: dict[str, object]) -> str | None:
    return label(entry, "updated")
