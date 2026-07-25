"""raw_payloads: the database index into the on-disk immutable archive."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class RawPayloadRow(Base):
    __tablename__ = "raw_payloads"

    sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_key: Mapped[str] = mapped_column(String(64), index=True)
    url: Mapped[str]
    external_id: Mapped[str | None] = mapped_column(String(256))
    request_hints: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    media_type: Mapped[str] = mapped_column(String(128))
    size_bytes: Mapped[int]
    http_status: Mapped[int | None]
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    relative_path: Mapped[str]
    adapter_version: Mapped[int]
