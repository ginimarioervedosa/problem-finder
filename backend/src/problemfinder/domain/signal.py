"""The problem signal: one piece of evidence that someone has a problem.

Two kinds share a common core. A verbatim signal is one person's own words
(a forum post, an ombudsman decision, a review). An aggregate signal is a
published statistic (a firm's complaint count for a half-year). Drill-down to
individuals only exists for verbatims; aggregates corroborate volume and trend.
"""

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, JsonValue

from problemfinder.domain.provenance import Provenance


class SignalKind(StrEnum):
    VERBATIM = "verbatim"
    AGGREGATE = "aggregate"


class SignalCore(BaseModel):
    """Fields every signal carries, whatever the source."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    source_key: str
    external_id: str
    url: HttpUrl
    published_at: AwareDatetime | None
    retrieved_at: AwareDatetime
    title: str | None
    body: str
    language: str = "en"
    firm_name: str | None = None
    category: str | None = None
    extras: dict[str, JsonValue] = Field(default_factory=dict)
    provenance: Provenance


class VerbatimSignal(SignalCore):
    """One person's own words, unmodified."""

    kind: Literal[SignalKind.VERBATIM] = SignalKind.VERBATIM
    author_handle: str | None = None


class AggregateSignal(SignalCore):
    """A published statistic covering an observation window."""

    kind: Literal[SignalKind.AGGREGATE] = SignalKind.AGGREGATE
    period_start: date
    period_end: date
    volume: int = Field(ge=0)
    upheld_share: float | None = Field(default=None, ge=0.0, le=1.0)
    denominator: int | None = Field(default=None, ge=0)


ProblemSignal = Annotated[VerbatimSignal | AggregateSignal, Field(discriminator="kind")]
