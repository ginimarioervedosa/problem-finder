"""Policy-configured HTTP client shared by all adapters.

One bucket per source key, held at module level, so every request a source
makes in this process (discovery pages and payload fetches alike) shares one
rate limit and one identifying user agent. Adapters never construct a bare
httpx client.
"""

import httpx

from problemfinder.domain.source_policy import SourcePolicy
from problemfinder.sources.rate_limiter import TokenBucket

IDENTIFYING_USER_AGENT = (
    "problem-finder/0.1 (single-user research tool; contact: mario.ervedosa@thegini.co.uk)"
)

_buckets: dict[str, TokenBucket] = {}


def client_for(source_key: str, policy: SourcePolicy) -> httpx.AsyncClient:
    """An AsyncClient that waits on the source's shared token bucket per request."""
    bucket = _buckets.setdefault(source_key, TokenBucket(policy.rate_limit))

    async def throttle(_request: httpx.Request) -> None:
        await bucket.acquire()

    return httpx.AsyncClient(
        headers={"User-Agent": policy.user_agent},
        event_hooks={"request": [throttle]},
        follow_redirects=True,
        timeout=30.0,
    )
