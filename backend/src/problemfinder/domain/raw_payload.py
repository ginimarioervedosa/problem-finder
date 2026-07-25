"""Metadata for one immutably archived raw payload.

The bytes live on disk, content-addressed by sha256; this record is the
database's index into that archive.
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class RawPayloadMeta(BaseModel):
    model_config = ConfigDict(frozen=True)

    sha256: str = Field(min_length=64, max_length=64)
    source_key: str
    url: str
    media_type: str
    size_bytes: int = Field(ge=0)
    http_status: int | None = None
    fetched_at: AwareDatetime
    relative_path: str
    adapter_version: int
