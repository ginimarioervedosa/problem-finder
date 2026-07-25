"""Provenance: the trail from any signal back to its immutable raw payload."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict


class Provenance(BaseModel):
    """Every signal traces to an archived payload and the run that produced it.

    The raw payload is stored write-once and content-addressed, so bumping an
    adapter's version and replaying the archive (`pf reparse`) can regenerate
    every signal without refetching anything.
    """

    model_config = ConfigDict(frozen=True)

    raw_payload_sha256: str
    adapter_version: int
    ingestion_run_id: UUID
    fetched_at: AwareDatetime
