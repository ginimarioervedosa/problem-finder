"""Deterministic signal identity, shared by every adapter.

A signal's id is a UUIDv5 of (source_key, external_id), so reingesting or
reparsing the same evidence always produces the same id, and idempotence falls
out of the identity scheme rather than being bolted on.
"""

import hashlib
from uuid import UUID, uuid5

_NAMESPACE = uuid5(UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8"), "problemfinder")


def signal_id_for(source_key: str, external_id: str) -> UUID:
    """Stable id for one piece of evidence within one source."""
    return uuid5(_NAMESPACE, f"{source_key}:{external_id}")


def content_fingerprint(source_key: str, external_id: str, body: str) -> str:
    """Hash used to detect re-published content changing under a stable id."""
    digest = hashlib.sha256(f"{source_key}|{external_id}|{body}".encode())
    return digest.hexdigest()
