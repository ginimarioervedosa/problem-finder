"""Per-source resume point for incremental ingestion."""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue


class Cursor(BaseModel):
    """Opaque to everything except the adapter that owns it.

    The pipeline stores and replays `state` verbatim; only the adapter whose
    `source_key` matches interprets its contents.
    """

    model_config = ConfigDict(frozen=True)

    source_key: str
    state: dict[str, JsonValue] = Field(default_factory=dict)
    updated_at: AwareDatetime
