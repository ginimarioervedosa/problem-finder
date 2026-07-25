"""Transient failures retry with backoff; persistent ones propagate."""

import httpx
import pytest

from problemfinder.domain.source_policy import RateLimit
from problemfinder.sources.rate_limiter import TokenBucket
from problemfinder.sources.retry import MAX_ATTEMPTS, RetryingTransport


class ScriptedTransport(httpx.AsyncBaseTransport):
    """Plays back a fixed sequence of responses or transport errors."""

    def __init__(self, *outcomes: int | httpx.TransportError) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, httpx.TransportError):
            raise outcome
        return httpx.Response(outcome, request=request)


def make_transport(
    *outcomes: int | httpx.TransportError,
) -> tuple[RetryingTransport, ScriptedTransport]:
    inner = ScriptedTransport(*outcomes)
    bucket = TokenBucket(RateLimit(requests=1000, per_seconds=0.001))
    return RetryingTransport(inner, bucket, base_delay=0.0), inner


async def send(transport: RetryingTransport) -> httpx.Response:
    async with httpx.AsyncClient(transport=transport) as client:
        return await client.get("https://example.org/")


async def test_a_retryable_status_is_retried_until_success() -> None:
    transport, inner = make_transport(503, 429, 200)
    response = await send(transport)
    assert response.status_code == 200
    assert inner.calls == 3


async def test_a_transport_error_is_retried() -> None:
    transport, inner = make_transport(httpx.ConnectError("refused"), 200)
    response = await send(transport)
    assert response.status_code == 200
    assert inner.calls == 2


async def test_gives_up_after_max_attempts_and_returns_the_last_response() -> None:
    transport, inner = make_transport(503, 503, 503)
    response = await send(transport)
    assert response.status_code == 503
    assert inner.calls == MAX_ATTEMPTS


async def test_a_persistent_transport_error_propagates() -> None:
    errors = [httpx.ConnectError("refused") for _ in range(MAX_ATTEMPTS)]
    transport, inner = make_transport(*errors)
    with pytest.raises(httpx.ConnectError):
        await send(transport)
    assert inner.calls == MAX_ATTEMPTS


async def test_a_plain_failure_status_is_not_retried() -> None:
    transport, inner = make_transport(404)
    response = await send(transport)
    assert response.status_code == 404
    assert inner.calls == 1
