"""cursors: one resume point per source, replaced after every successful run."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class CursorRow(Base):
    __tablename__ = "cursors"

    source_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[dict[str, object]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
