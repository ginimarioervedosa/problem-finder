"""Bounded retry with exponential backoff for transient HTTP failures.

Wraps the real transport, so every request an adapter makes (discovery pages
and payload fetches alike) retries the same way. The source's token bucket is
acquired per attempt: a retry queues behind the rate limit like any request.
A failure that survives all attempts propagates and lands in the run's error
ledger; it never aborts the run.
"""

import asyncio

import httpx

from problemfinder.sources.rate_limiter import TokenBucket

MAX_ATTEMPTS = 3
_BASE_DELAY_SECONDS = 1.0
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class RetryingTransport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        bucket: TokenBucket,
        base_delay: float = _BASE_DELAY_SECONDS,
    ) -> None:
        self._inner = inner
        self._bucket = bucket
        self._base_delay = base_delay

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        attempts = 0
        while True:
            attempts += 1
            await self._bucket.acquire()
            try:
                response = await self._inner.handle_async_request(request)
            except httpx.TransportError:
                if attempts >= MAX_ATTEMPTS:
                    raise
            else:
                if response.status_code not in _RETRYABLE_STATUSES or attempts >= MAX_ATTEMPTS:
                    return response
                await response.aclose()
            await asyncio.sleep(self._base_delay * 2 ** (attempts - 1))

    async def aclose(self) -> None:
        await self._inner.aclose()
