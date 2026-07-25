"""The token bucket paces requests to the declared limit."""

import time

from problemfinder.domain.source_policy import RateLimit
from problemfinder.sources.rate_limiter import TokenBucket


async def test_burst_is_immediate_then_paced() -> None:
    bucket = TokenBucket(RateLimit(requests=10, per_seconds=1.0, burst=2))
    started = time.monotonic()
    await bucket.acquire()
    await bucket.acquire()
    burst_elapsed = time.monotonic() - started
    await bucket.acquire()
    paced_elapsed = time.monotonic() - started
    assert burst_elapsed < 0.05
    assert paced_elapsed >= 0.08


async def test_tokens_refill_up_to_capacity_only() -> None:
    bucket = TokenBucket(RateLimit(requests=100, per_seconds=1.0, burst=1))
    await bucket.acquire()
    time.sleep(0.05)
    started = time.monotonic()
    await bucket.acquire()
    await bucket.acquire()
    assert time.monotonic() - started >= 0.005
