"""The committee evidence compliance declaration, reviewed 2026-07-26."""

from datetime import date

from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)
from problemfinder.sources.http import IDENTIFYING_USER_AGENT

COMMITTEE_EVIDENCE_POLICY = SourcePolicy(
    method=IngestionMethod.OFFICIAL_API,
    robots_status=RobotsStatus.NOT_APPLICABLE,  # official API host serves no robots.txt (404)
    terms_reviewed=date(2026, 7, 26),
    terms_notes=(
        "Reviewed 2026-07-26: committees-api.parliament.uk is UK Parliament's "
        "documented public committees API (contact "
        "softwareengineering@parliament.uk per its OpenAPI spec); it answers "
        "plain HTTP clients while the committees website sits behind a "
        "Cloudflare challenge, so only the API is used. Written evidence is "
        "parliamentary copyright published under the Open Parliament Licence "
        "v3.0 (text verified via SPDX OPL-UK-3.0), which grants copying, "
        "publishing, adaptation and commercial use with attribution; every "
        "signal cites its submission reference and page URL."
    ),
    rate_limit=RateLimit(requests=1, per_seconds=2.0),
    user_agent=IDENTIFYING_USER_AGENT,
)
