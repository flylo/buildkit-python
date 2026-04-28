from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import TypeVar

T = TypeVar("T")
LOGGER = logging.getLogger(__name__)


async def time_function[T](
    func: Callable[[], Awaitable[T]],
    func_name: str = "Function",
) -> T:
    start = perf_counter()
    result = await func()
    elapsed_ms = (perf_counter() - start) * 1000
    LOGGER.info("%s execution time: %s milliseconds", func_name, elapsed_ms)
    return result
