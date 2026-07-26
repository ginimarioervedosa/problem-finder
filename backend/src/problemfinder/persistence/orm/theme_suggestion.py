"""theme_suggestions: clustering proposals and their review decisions.

Member and representative ids are JSONB arrays of UUID strings: clusters are
read and decided whole, never joined per member, and the corpus is
single-user scale. Undecided rows are replaced wholesale on recluster.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class ThemeSuggestionRow(Base):
    __tablename__ = "theme_suggestions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    method: Mapped[str] = mapped_column(String(64), index=True)
    cluster_key: Mapped[int]
    label: Mapped[str] = mapped_column(String(128))
    top_terms: Mapped[list[str]] = mapped_column(JSONB)
    size: Mapped[int]
    member_signal_ids: Mapped[list[str]] = mapped_column(JSONB)
    representative_signal_ids: Mapped[list[str]] = mapped_column(JSONB)
    suggested_theme: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), index=True)
    mapped_theme: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
