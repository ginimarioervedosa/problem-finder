"""The compliance declaration every source adapter must ship.

The declaration is data; enforcement lives in ingestion.compliance, which
refuses to run any adapter whose policy fails the gate. Lawfulness is a code
path, not a judgement call repeated per session.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class IngestionMethod(StrEnum):
    OFFICIAL_API = "official_api"
    BULK_DOWNLOAD = "bulk_download"
    SCRAPE = "scrape"
    MANUAL_IMPORT = "manual_import"


class RobotsStatus(StrEnum):
    ALLOWED = "allowed"
    DISALLOWED = "disallowed"
    NOT_APPLICABLE = "not_applicable"


class RateLimit(BaseModel):
    """At most `requests` requests per `per_seconds` window."""

    model_config = ConfigDict(frozen=True)

    requests: int = Field(ge=1)
    per_seconds: float = Field(gt=0.0)
    burst: int = Field(default=1, ge=1)


class SourcePolicy(BaseModel):
    """One per adapter: how this source may lawfully be collected.

    `terms_reviewed` is the date a human last read robots.txt and the site's
    terms; `terms_notes` records where they live and what they permit, so the
    review is auditable without leaving the code.
    """

    model_config = ConfigDict(frozen=True)

    method: IngestionMethod
    robots_status: RobotsStatus
    terms_reviewed: date
    terms_notes: str
    rate_limit: RateLimit
    user_agent: str
    requires_browser: bool = False
