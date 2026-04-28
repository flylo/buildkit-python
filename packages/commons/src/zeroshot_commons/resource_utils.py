from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")
CLOSER_FUNCTION_TIMEOUT = 10.0
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CloseableResource[T]:
    resource: T
    closing_function: Callable[[T], Awaitable[Any]]


async def with_timeout[T](awaitable: Awaitable[T], timeout_seconds: float) -> T:
    return await asyncio.wait_for(awaitable, timeout=timeout_seconds)


class Closer:
    def __init__(self) -> None:
        self._closeable_resources: list[CloseableResource[Any]] = []

    @classmethod
    def create(cls, *closeables: CloseableResource[Any]) -> Closer:
        closer = cls()
        closer._closeable_resources = list(closeables)
        return closer

    def register_shutdown_hook(self, closeable: CloseableResource[Any]) -> None:
        self._closeable_resources.append(closeable)

    async def close(self) -> None:
        for closeable in self._closeable_resources:
            resource_name = type(closeable.resource).__name__
            LOGGER.info("Closing resource", extra={"resource_name": resource_name})
            try:
                await with_timeout(
                    self._close_with_warning(closeable, resource_name),
                    CLOSER_FUNCTION_TIMEOUT,
                )
            except TimeoutError:
                LOGGER.warning(
                    "Timed out while closing resource",
                    extra={"resource_name": resource_name},
                )
            LOGGER.info("Successfully closed resource", extra={"resource_name": resource_name})

    async def _close_with_warning(
        self,
        closeable: CloseableResource[Any],
        resource_name: str,
    ) -> None:
        try:
            await closeable.closing_function(closeable.resource)
        except Exception:
            LOGGER.warning(
                "Exception while closing resource",
                exc_info=True,
                extra={"resource_name": resource_name},
            )
