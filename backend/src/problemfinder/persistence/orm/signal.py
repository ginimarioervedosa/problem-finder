"""signals: one table for both kinds, discriminated by `kind`.

Aggregate-only and verbatim-only fields are nullable columns; the mapping
parity test asserts this table and the domain union never drift apart.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Computed, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class SignalRow(Base):
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("source_key", "external_id"),
        Index("ix_signals_search_tsv", "search_tsv", postgresql_using="gin"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str] = mapped_column(String(256))
    kind: Mapped[str] = mapped_column(String(16), index=True)
    url: Mapped[str]
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    title: Mapped[str | None]
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(16))
    firm_name: Mapped[str | None] = mapped_column(String(256), index=True)
    # Text, not a guessed cap: committee inquiry titles and joint-author
    # handles exceed 128 and the domain model imposes no length.
    category: Mapped[str | None] = mapped_column(Text, index=True)
    extras: Mapped[dict[str, object]] = mapped_column(JSONB)

    # verbatim-only
    author_handle: Mapped[str | None] = mapped_column(Text)

    # aggregate-only
    period_start: Mapped[date | None]
    period_end: Mapped[date | None]
    volume: Mapped[int | None]
    upheld_share: Mapped[float | None]
    denominator: Mapped[int | None]

    # provenance, flattened
    raw_payload_sha256: Mapped[str] = mapped_column(ForeignKey("raw_payloads.sha256"))
    adapter_version: Mapped[int]
    ingestion_run_id: Mapped[UUID] = mapped_column(ForeignKey("ingestion_runs.id"))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    dedupe_hash: Mapped[str] = mapped_column(String(64), index=True)

    # Full-text search over title and body; computed by Postgres, never inserted.
    search_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(title, '') || ' ' || body)", persisted=True),
    )
