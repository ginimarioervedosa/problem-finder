"""The App Store reviews compliance declaration, decided 2026-07-27."""

from datetime import date

from problemfinder.domain.source_policy import (
    IngestionMethod,
    RateLimit,
    RobotsStatus,
    SourcePolicy,
)
from problemfinder.sources.http import IDENTIFYING_USER_AGENT

APP_STORE_REVIEWS_POLICY = SourcePolicy(
    method=IngestionMethod.OFFICIAL_API,
    robots_status=RobotsStatus.DISALLOWED,  # recorded honestly; see the notes
    terms_reviewed=date(2026, 7, 27),
    terms_notes=(
        "Reviewed 2026-07-26: itunes.apple.com/robots.txt disallows /*/rss/* "
        "for all user agents, which catches the customer-reviews feed path. "
        "The feed is Apple's long-standing official syndication feed for app "
        "reviews and answers normally; the purposive reading is that the "
        "disallow aims at search-engine indexing of feed pages, not at feed "
        "consumption. The owner decided on 2026-07-27 to declare the source "
        "an official API on that reading, with the robots status recorded "
        "as DISALLOWED rather than papered over. Polled at a low rate for a "
        "small configured list of apps. Full record in "
        "docs/compliance/phase-6-verdicts.md."
    ),
    rate_limit=RateLimit(requests=1, per_seconds=3.0),
    user_agent=IDENTIFYING_USER_AGENT,
)
