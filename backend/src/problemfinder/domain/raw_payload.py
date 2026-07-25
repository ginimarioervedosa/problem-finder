"""Metadata for one immutably archived raw payload.

The bytes live on disk, content-addressed by sha256; this record is the
database's index into that archive. It also captures the work item that
produced the payload (external_id, request_hints), so `pf reparse` can
reconstruct the parse input without refetching anything.
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue


class RawPayloadMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    sha256: str = Field(min_length=64, max_length=64)
    source_key: str
    url: str
    external_id: str | None = None  # None only for payloads archived before capture existed
    request_hints: dict[str, JsonValue] = Field(default_factory=dict)
    media_type: str
    size_bytes: int = Field(ge=0)
    http_status: int | None = None
    fetched_at: AwareDatetime
    relative_path: str
    adapter_version: int
