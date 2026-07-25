"""Write-once, content-addressed raw payload archive.

Every payload is archived before parsing; the archive is the replay substrate
that lets `pf reparse` regenerate all signals without refetching. Files are
stored at <archive_dir>/<source>/<sha256[:2]>/<sha256>, written atomically,
then made read-only. Nothing here ever truncates or deletes.
"""

import hashlib
from pathlib import Path

from problemfinder.domain.raw_payload import RawPayloadMeta
from problemfinder.settings import get_settings
from problemfinder.sources.protocol import RawDocument

_READ_ONLY = 0o444


def store(raw: RawDocument, source_key: str, adapter_version: int) -> RawPayloadMeta:
    """Archive one payload; a payload already present is verified, not rewritten."""
    sha256 = hashlib.sha256(raw.content).hexdigest()
    relative = Path(source_key) / sha256[:2] / sha256
    target = get_settings().archive_dir / relative
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        scratch = target.with_suffix(".part")
        scratch.unlink(missing_ok=True)
        scratch.write_bytes(raw.content)
        scratch.chmod(_READ_ONLY)
        scratch.rename(target)
    return RawPayloadMeta(
        sha256=sha256,
        source_key=source_key,
        url=str(raw.work_item.url),
        media_type=raw.media_type,
        size_bytes=len(raw.content),
        http_status=raw.http_status,
        fetched_at=raw.fetched_at,
        relative_path=str(relative),
        adapter_version=adapter_version,
    )


def load(relative_path: str) -> bytes:
    """Read one archived payload back for reparse."""
    return (get_settings().archive_dir / relative_path).read_bytes()
