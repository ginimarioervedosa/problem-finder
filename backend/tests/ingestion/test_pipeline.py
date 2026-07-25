"""Pipeline invariants: stage order, idempotence, and error isolation."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select

from problemfinder.domain.raw_payload import RawPayloadMeta
from problemfinder.ingestion import archive, pipeline
from problemfinder.persistence.orm import SignalRow
from problemfinder.sources import registry
from problemfinder.sources.protocol import RawDocument
from problemfinder.sources.registry import _registry
from tests.support.stub_source import StubSource

pytestmark = pytest.mark.db


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> Generator[StubSource]:
    """Register a stub adapter and record archive.store into its event log."""
    instance = StubSource(item_ids=("item-1", "boom", "item-2"))
    _registry["stub"] = instance
    real_store = archive.store

    def recording_store(raw: RawDocument, source_key: str, adapter_version: int) -> RawPayloadMeta:
        instance.events.append(("archive", raw.work_item.external_id))
        return real_store(raw, source_key, adapter_version)

    monkeypatch.setattr(archive, "store", recording_store)
    yield instance
    del _registry["stub"]


async def test_stage_order_and_error_isolation(
    stub: StubSource, pipeline_db: Engine, tmp_archive: Path
) -> None:
    run = await pipeline.run_source("stub")

    per_item = [e[0] for e in stub.events if e[1] == "item-1"]
    assert per_item == ["discover", "fetch", "archive", "parse", "normalise"]

    boom_stages = [e[0] for e in stub.events if e[1] == "boom"]
    assert boom_stages == ["discover", "fetch"]
    assert run.errors == ["boom: synthetic fetch failure"]
    assert run.fetched == 2
    assert run.stored_new == 2
    assert run.finished_at is not None
    assert run.cursor_after is not None


async def test_reingest_is_idempotent(
    stub: StubSource, pipeline_db: Engine, tmp_archive: Path
) -> None:
    first = await pipeline.run_source("stub", limit=1)
    second = await pipeline.run_source("stub", limit=1)
    assert first.stored_new == 1
    assert second.stored_new == 0
    assert second.deduplicated == 1
    with pipeline_db.connect() as connection:
        count = connection.execute(select(func.count()).select_from(SignalRow)).scalar()
    assert count == 1


async def test_unknown_source_fails_loudly(pipeline_db: Engine) -> None:
    with pytest.raises(registry.UnknownSourceError):
        await pipeline.run_source("nope")
