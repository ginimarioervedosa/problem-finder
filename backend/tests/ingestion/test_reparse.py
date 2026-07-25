"""Reparse invariants: archive-only replay, stable ids, overwritten content."""

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import ClassVar

import pytest
import respx
from sqlalchemy import Engine, select, text

from problemfinder.domain.identity import signal_id_for
from problemfinder.ingestion import pipeline, reparse
from problemfinder.persistence.orm import SignalRow
from problemfinder.sources.protocol import ParsedRecord, RawDocument
from problemfinder.sources.registry import _registry
from tests.support.stub_source import StubSource

pytestmark = pytest.mark.db


class ReparsedStub(StubSource):
    """Version 2 of the stub: same identities, a different reading of the bytes."""

    version: ClassVar[int] = 2

    def parse(self, raw: RawDocument) -> Iterator[ParsedRecord]:
        yield ParsedRecord(
            external_id=raw.work_item.external_id,
            fields={"text": raw.content.decode().upper()},
        )


@pytest.fixture
def stub() -> Generator[StubSource]:
    instance = StubSource(item_ids=("item-1", "item-2"))
    _registry["stub"] = instance
    yield instance
    del _registry["stub"]


async def test_parser_change_updates_signals_from_archive_alone(
    stub: StubSource, pipeline_db: Engine, tmp_archive: Path
) -> None:
    ingested = await pipeline.run_source("stub")
    assert ingested.stored_new == 2

    _registry["stub"] = ReparsedStub(item_ids=("item-1", "item-2"))
    with respx.mock:  # no routes registered: any HTTP request would fail loudly
        run = reparse.reparse_source("stub")

    assert run.fetched == 0
    assert run.parsed == 2
    assert run.stored_new == 2
    assert run.errors == []
    with pipeline_db.connect() as connection:
        rows = connection.execute(
            select(SignalRow.id, SignalRow.body, SignalRow.adapter_version).order_by(
                SignalRow.external_id
            )
        ).fetchall()
    assert [row.id for row in rows] == [
        signal_id_for("stub", "item-1"),
        signal_id_for("stub", "item-2"),
    ]
    assert [row.body for row in rows] == ["PAYLOAD FOR ITEM-1", "PAYLOAD FOR ITEM-2"]
    assert all(row.adapter_version == 2 for row in rows)


async def test_reparse_is_idempotent(
    stub: StubSource, pipeline_db: Engine, tmp_archive: Path
) -> None:
    await pipeline.run_source("stub")
    first = reparse.reparse_source("stub")
    second = reparse.reparse_source("stub")
    assert first.stored_new == second.stored_new == 2
    with pipeline_db.connect() as connection:
        count = len(connection.execute(select(SignalRow.id)).fetchall())
    assert count == 2


async def test_uncaptured_payload_lands_in_the_error_ledger(
    stub: StubSource, pipeline_db: Engine, tmp_archive: Path
) -> None:
    await pipeline.run_source("stub", limit=1)
    with pipeline_db.begin() as connection:
        connection.execute(text("update raw_payloads set external_id = null"))

    run = reparse.reparse_source("stub")
    assert run.parsed == 0
    assert run.stored_new == 0
    assert len(run.errors) == 1
    assert "predates work-item capture" in run.errors[0]
