from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def eventually[T](
    runnable: Callable[[], Awaitable[T]],
    interval_ms: int = 100,
    duration_ms: int = 10_000,
) -> T:
    """Retry *runnable* until it succeeds or *duration_ms* elapses.

    Useful for polling eventual-consistency assertions in integration tests.
    """
    start = asyncio.get_event_loop().time()
    deadline = start + duration_ms / 1000.0
    last_error: BaseException | None = None

    while True:
        try:
            return await runnable()
        except Exception as exc:
            last_error = exc
            now = asyncio.get_event_loop().time()
            if now >= deadline:
                break
            await asyncio.sleep(interval_ms / 1000.0)

    raise last_error  # type: ignore[misc]


async def timeout(millis: int) -> None:
    """Sleep for *millis* milliseconds."""
    await asyncio.sleep(millis / 1000.0)
