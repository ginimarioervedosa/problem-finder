"""One pipeline execution: the provenance and observability record."""

from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from problemfinder.domain.cursor import Cursor


class IngestionRun(BaseModel):
    """Counts and cursor movement for a single run of one source."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    source_key: str
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    cursor_before: Cursor | None = None
    cursor_after: Cursor | None = None
    fetched: int = Field(default=0, ge=0)
    parsed: int = Field(default=0, ge=0)
    stored_new: int = Field(default=0, ge=0)
    deduplicated: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
