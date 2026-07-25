"""The Reddit compliance declaration, reviewed 2026-07-25."""

from datetime import date

from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)

REDDIT_POLICY = SourcePolicy(
    method=IngestionMethod.OFFICIAL_API,
    robots_status=RobotsStatus.NOT_APPLICABLE,  # official API, not crawling
    terms_reviewed=date(2026, 7, 25),
    terms_notes=(
        "Reviewed 2026-07-25 against the Reddit Data API Terms and the "
        "Responsible Builder Policy (support.reddithelp.com; primary pages "
        "are Cloudflare-gated to non-browser clients, so the review used "
        "the published terms as reported by multiple current secondary "
        "sources). The free tier permits non-commercial research at up to "
        "100 queries per minute per OAuth client; this tool is single-user, "
        "local, stores fetched content only for its own research index, "
        "never republishes, and never trains models on Reddit data. OAuth "
        "(script app) and a descriptive user agent are required; both are "
        "used. Reddit now gates new API access behind an approval request; "
        "completing registration and any approval step is the owner's "
        "action when creating the app credentials."
    ),
    rate_limit=RateLimit(requests=60, per_seconds=60.0),  # well under the 100 QPM cap
    user_agent=(
        "script:problem-finder:0.1 (single-user research tool; "
        "contact: mario.ervedosa@thegini.co.uk)"
    ),
)
