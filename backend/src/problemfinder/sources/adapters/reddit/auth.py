"""Application-only OAuth against Reddit: one cached bearer token per process."""

from datetime import UTC, datetime, timedelta

from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.settings import get_settings
from problemfinder.sources.http import client_for

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_EXPIRY_MARGIN_SECONDS = 60.0

_cached: tuple[str, datetime] | None = None


class RedditCredentialsError(RuntimeError):
    """No OAuth credentials in the environment; the run cannot start."""


async def bearer_token(source_key: str, policy: SourcePolicy) -> str:
    global _cached  # noqa: PLW0603 -- one token per process, like http._buckets
    now = datetime.now(tz=UTC)
    if _cached is not None and _cached[1] > now:
        return _cached[0]
    settings = get_settings()
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        raise RedditCredentialsError(
            "set PF_REDDIT_CLIENT_ID and PF_REDDIT_CLIENT_SECRET in .env "
            "(create a script app at reddit.com/prefs/apps)"
        )
    async with client_for(source_key, policy) as client:
        response = await client.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
        )
        response.raise_for_status()
        payload = response.json()
    lifetime = float(payload.get("expires_in", 3600.0)) - _EXPIRY_MARGIN_SECONDS
    _cached = (str(payload["access_token"]), now + timedelta(seconds=lifetime))
    return _cached[0]
