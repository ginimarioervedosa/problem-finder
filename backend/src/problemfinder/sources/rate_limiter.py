"""Async token bucket enforcing a declared RateLimit.

Lives in the sources layer, not ingestion, because throttling must wrap every
outbound request an adapter makes, including discovery-time page fetches, and
the layering contract forbids sources importing ingestion.
"""

import asyncio
import time

from problemfinder.domain.source_policy import RateLimit


class TokenBucket:
    """Classic token bucket: capacity = burst, refill = requests/per_seconds."""

    def __init__(self, limit: RateLimit) -> None:
        self._capacity = float(limit.burst)
        self._tokens = float(limit.burst)
        self._refill_per_second = limit.requests / limit.per_seconds
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                shortfall = (1.0 - self._tokens) / self._refill_per_second
                await asyncio.sleep(shortfall)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_per_second)
