"""signal_enrichments: versioned derived attributes; recompute appends versions."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from problemfinder.persistence.orm.base import Base


class SignalEnrichmentRow(Base):
    __tablename__ = "signal_enrichments"

    signal_id: Mapped[UUID] = mapped_column(ForeignKey("signals.id"), primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    theme: Mapped[str | None] = mapped_column(String(128), index=True)
    sub_theme: Mapped[str | None] = mapped_column(String(128))
    product_domain: Mapped[str | None] = mapped_column(String(64), index=True)
    severity: Mapped[float | None]
    severity_basis: Mapped[str | None]
    monetary_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    monetary_currency: Mapped[str | None] = mapped_column(String(3))
    resolution: Mapped[str | None] = mapped_column(String(32))
    geography: Mapped[str | None] = mapped_column(String(16))
    segment: Mapped[str | None] = mapped_column(String(32))
    sentiment: Mapped[float | None]
    method: Mapped[str] = mapped_column(String(64))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
