from __future__ import annotations

from dataclasses import dataclass

import pytest

from zeroshot_commons import RedisClientPool, RedisConnectionConfig


def test_redis_connection_config_generates_expected_url_and_queue_connection() -> None:
    config = RedisConnectionConfig.from_mapping(
        {
            "host": "localhost",
            "port": 6379,
            "poolSize": 2,
            "db": 1,
        }
    )

    assert config.url == "redis://localhost:6379/1"
    assert config.queue_connection() == {"host": "localhost", "port": 6379, "db": 1}


@pytest.mark.asyncio
async def test_redis_client_pool_acquire_release_and_close() -> None:
    closed: list[str] = []

    @dataclass
    class FakeClient:
        name: str

        async def aclose(self) -> None:
            closed.append(self.name)

    counter = 0

    def factory(connection_config: RedisConnectionConfig) -> FakeClient:
        nonlocal counter
        counter += 1
        return FakeClient(name=f"{connection_config.host}-{counter}")

    pool = RedisClientPool(
        connection_config=RedisConnectionConfig(host="localhost", port=6379, pool_size=2),
        client_factory=factory,
    )

    client = await pool.acquire()
    pool.release(client)

    result = await pool.with_connection(lambda acquired: acquired.name)
    assert result.startswith("localhost-")

    await pool.close()
    assert closed == ["localhost-1", "localhost-2"]
