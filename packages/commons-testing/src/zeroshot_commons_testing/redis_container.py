from __future__ import annotations

import logging

from testcontainers.redis import RedisContainer as _RedisContainer

from zeroshot_commons import RedisConnectionConfig

logger = logging.getLogger(__name__)

_IMAGE = "redis:8.4.2"


class RedisContainer:
    """Manages a disposable Redis container for integration tests."""

    def __init__(self) -> None:
        self._container = _RedisContainer(image=_IMAGE).with_bind_ports(6379, 0)
        self._started: _RedisContainer | None = None

    async def start(self) -> None:
        self._started = self._container.start()

    async def stop(self) -> None:
        if self._started is not None:
            self._started.stop()
            self._started = None

    def get_connection_config(self) -> RedisConnectionConfig:
        if self._started is None:
            raise RuntimeError("Container has not been started")
        host = self._started.get_container_host_ip()
        port = int(self._started.get_exposed_port(6379))
        return RedisConnectionConfig(host=host, port=port)
