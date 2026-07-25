"""ingestion_runs: one row per pipeline execution."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class IngestionRunRow(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor_before: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    cursor_after: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    fetched: Mapped[int]
    parsed: Mapped[int]
    stored_new: Mapped[int]
    deduplicated: Mapped[int]
    errors: Mapped[list[str]] = mapped_column(JSONB)
