from __future__ import annotations

from collections.abc import AsyncIterator

from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from zeroshot_commons import PostgresConnectionConfig, RedisClientPool, RedisConnectionConfig


def build_redis_client(connection_config: RedisConnectionConfig) -> Redis:
    return Redis.from_url(
        connection_config.url,
        decode_responses=connection_config.decode_responses,
    )


async def init_redis_client(connection_config: RedisConnectionConfig) -> AsyncIterator[Redis]:
    client = build_redis_client(connection_config)
    await client.ping()
    try:
        yield client
    finally:
        await client.aclose()


def build_postgres_engine(connection_config: PostgresConnectionConfig) -> AsyncEngine:
    engine_options: dict[str, object] = {
        "echo": connection_config.logging,
        "pool_pre_ping": True,
    }
    if connection_config.pool_max is not None:
        engine_options["pool_size"] = connection_config.pool_max
    if connection_config.pool_acquire is not None:
        engine_options["pool_timeout"] = connection_config.pool_acquire / 1000
    return create_async_engine(
        connection_config.sqlalchemy_url(),
        **engine_options,
    )


async def init_postgres_engine(
    connection_config: PostgresConnectionConfig,
) -> AsyncIterator[AsyncEngine]:
    engine = build_postgres_engine(connection_config)
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    try:
        yield engine
    finally:
        await engine.dispose()


def build_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def build_redis_client_pool(
    connection_config: RedisConnectionConfig,
) -> RedisClientPool:
    return RedisClientPool(
        connection_config=connection_config,
        client_factory=build_redis_client,
    )


class RedisConnectionContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    connection_config = providers.Factory(
        RedisConnectionConfig.from_mapping,
        data=config,
    )
    client = providers.Resource(
        init_redis_client,
        connection_config=connection_config,
    )
    client_pool = providers.Singleton(
        build_redis_client_pool,
        connection_config=connection_config,
    )


class PostgresConnectionContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    connection_config = providers.Factory(
        PostgresConnectionConfig.from_mapping,
        data=config,
    )
    engine = providers.Resource(
        init_postgres_engine,
        connection_config=connection_config,
    )
    session_factory = providers.Factory(
        build_session_factory,
        engine=engine,
    )


class CommonsInfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    redis = providers.Container(
        RedisConnectionContainer,
        config=config.redis,
    )
    postgres = providers.Container(
        PostgresConnectionContainer,
        config=config.postgres,
    )
