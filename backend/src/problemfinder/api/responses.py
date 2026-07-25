"""API-only response wrappers around the domain models."""

from pydantic import BaseModel

from problemfinder.domain.ingestion_run import IngestionRun
from problemfinder.domain.signal import AggregateSignal, VerbatimSignal
from problemfinder.domain.source_policy import SourcePolicy


class SignalPage(BaseModel):
    items: list[VerbatimSignal | AggregateSignal]
    total: int
    limit: int
    offset: int


class SourceInfo(BaseModel):
    key: str
    version: int
    enabled: bool
    policy: SourcePolicy
    last_run: IngestionRun | None
