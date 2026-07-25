"""Derived attributes layered over signals, never authoritative.

Every enrichment row records the method that produced it and a version;
recomputing the lot from stored signals is one command (`pf enrich run
--recompute`), because categorisation opinions change more often than facts.
"""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from problemfinder.domain.dimensions import ProductDomain, WealthSegment


class ResolutionStatus(StrEnum):
    UPHELD = "upheld"
    NOT_UPHELD = "not_upheld"
    SETTLED = "settled"
    PROACTIVELY_SETTLED = "proactively_settled"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"


class SignalEnrichment(BaseModel):
    """One versioned set of derived attributes for one signal."""

    model_config = ConfigDict(frozen=True)

    signal_id: UUID
    version: int = Field(ge=1)
    theme: str | None = None
    sub_theme: str | None = None
    product_domain: ProductDomain | None = None
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    severity_basis: str | None = None
    monetary_amount: Decimal | None = None
    monetary_currency: str | None = None
    resolution: ResolutionStatus | None = None
    geography: str | None = None
    segment: WealthSegment | None = None
    sentiment: float | None = Field(default=None, ge=-1.0, le=1.0)
    method: str
    computed_at: AwareDatetime
