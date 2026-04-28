from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar
from urllib.parse import quote_plus

from .application_config import ApplicationConfig
from .config_utils import load_config


T = TypeVar("T")


class AsyncClosable(Protocol):
    async def aclose(self) -> None: ...


@dataclass(frozen=True, slots=True)
class RedisConnectionConfig:
    host: str
    port: int
    pool_size: int | None = None
    db: int = 0
    username: str | None = None
    password: str | None = None
    ssl: bool = False
    decode_responses: bool = True

    REDIS_CONFIG_KEY = "redis"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RedisConnectionConfig":
        return cls(
            host=str(data["host"]),
            port=int(data["port"]),
            pool_size=int(data["poolSize"]) if data.get("poolSize") is not None else None,
            db=int(data.get("db", 0)),
            username=str(data["username"]) if data.get("username") is not None else None,
            password=str(data["password"]) if data.get("password") is not None else None,
            ssl=bool(data.get("ssl", False)),
            decode_responses=bool(data.get("decodeResponses", True)),
        )

    @classmethod
    def from_application_config(
        cls,
        application_config: ApplicationConfig,
    ) -> "RedisConnectionConfig":
        if not application_config.application_root:
            raise ValueError("application_root is required to load redis config")
        config: dict[str, Any] = load_config(
            application_config.application_root,
            cls.REDIS_CONFIG_KEY,
        )
        return cls.from_mapping(config)

    @property
    def url(self) -> str:
        scheme = "rediss" if self.ssl else "redis"
        auth = ""
        if self.username and self.password:
            auth = f"{quote_plus(self.username)}:{quote_plus(self.password)}@"
        elif self.password:
            auth = f":{quote_plus(self.password)}@"
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"

    def queue_connection(self) -> dict[str, Any]:
        connection = {"host": self.host, "port": self.port, "db": self.db}
        if self.username is not None:
            connection["username"] = self.username
        if self.password is not None:
            connection["password"] = self.password
        if self.ssl:
            connection["ssl"] = True
        return connection


class RedisClientPool:
    def __init__(
        self,
        connection_config: RedisConnectionConfig,
        client_factory: Callable[[RedisConnectionConfig], AsyncClosable],
        pool_size: int | None = None,
        acquire_timeout_seconds: float = 30.0,
    ) -> None:
        self.connection_config = connection_config
        self._client_factory = client_factory
        self._pool_size = pool_size or connection_config.pool_size or 10
        self._acquire_timeout_seconds = acquire_timeout_seconds
        self._available: asyncio.LifoQueue[AsyncClosable] = asyncio.LifoQueue(
            maxsize=self._pool_size
        )
        self._clients: list[AsyncClosable] = [
            self._client_factory(self.connection_config) for _ in range(self._pool_size)
        ]
        for client in self._clients:
            self._available.put_nowait(client)

    async def acquire(self) -> AsyncClosable:
        return await asyncio.wait_for(
            self._available.get(),
            timeout=self._acquire_timeout_seconds,
        )

    def release(self, client: AsyncClosable) -> None:
        self._available.put_nowait(client)

    async def with_connection(
        self,
        func: Callable[[AsyncClosable], Awaitable[T] | T],
    ) -> T:
        client = await self.acquire()
        try:
            result = func(client)
            if inspect.isawaitable(result):
                return await result
            return result
        finally:
            self.release(client)

    async def close(self) -> None:
        for client in self._clients:
            await client.aclose()
