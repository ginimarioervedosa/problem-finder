"""The archive is content-addressed, write-once, and read-only on disk."""

import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from problemfinder.ingestion.archive import load, store
from problemfinder.sources.protocol import RawDocument, WorkItem


def make_raw(content: bytes = b"payload") -> RawDocument:
    return RawDocument(
        work_item=WorkItem(external_id="x", url="https://example.org/x"),
        content=content,
        media_type="text/plain",
        fetched_at=datetime(2026, 7, 1, tzinfo=UTC),
    )


def test_store_is_content_addressed_and_read_only(tmp_archive: Path) -> None:
    meta = store(make_raw(), "stub", adapter_version=1)
    target = tmp_archive / meta.relative_path
    assert target.read_bytes() == b"payload"
    assert meta.relative_path == f"stub/{meta.sha256[:2]}/{meta.sha256}"
    assert meta.size_bytes == len(b"payload")
    mode = stat.S_IMODE(target.stat().st_mode)
    assert mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0
    with pytest.raises(PermissionError):
        target.open("ab")


def test_storing_identical_content_twice_is_one_file(tmp_archive: Path) -> None:
    first = store(make_raw(), "stub", adapter_version=1)
    second = store(make_raw(), "stub", adapter_version=1)
    assert first == second
    files = [p for p in tmp_archive.rglob("*") if p.is_file()]
    assert len(files) == 1


def test_different_content_never_collides(tmp_archive: Path) -> None:
    first = store(make_raw(b"one"), "stub", adapter_version=1)
    second = store(make_raw(b"two"), "stub", adapter_version=1)
    assert first.sha256 != second.sha256
    files = [p for p in tmp_archive.rglob("*") if p.is_file()]
    assert len(files) == 2


def test_load_round_trips(tmp_archive: Path) -> None:
    meta = store(make_raw(b"replay me"), "stub", adapter_version=1)
    assert load(meta.relative_path) == b"replay me"
