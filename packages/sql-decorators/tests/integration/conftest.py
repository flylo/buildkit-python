from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from zeroshot_commons_testing import PostgresContainer

_CREATE_TABLES = [
    """CREATE TABLE IF NOT EXISTS test (
        some_string VARCHAR(255) PRIMARY KEY,
        some_number NUMERIC NOT NULL UNIQUE,
        some_int BIGINT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS lol (
        some_string VARCHAR(255) PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS clazzes (
        some_string VARCHAR(255) PRIMARY KEY,
        some_number NUMERIC NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS broken (
        some_string VARCHAR(255) PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS nullable_table (
        some_id VARCHAR(255) PRIMARY KEY,
        some_nullable_string VARCHAR(255),
        some_nullable_number NUMERIC
    )""",
    """CREATE TABLE IF NOT EXISTS enum_table (
        some_id VARCHAR(255) PRIMARY KEY,
        some_enum VARCHAR(255)
    )""",
    """CREATE TABLE IF NOT EXISTS nested (
        id VARCHAR(255) PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS sub_type (
        name VARCHAR(255) PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS unconventional (
        some_1_name_2_with_3_numbers_4_intertwined VARCHAR(255) PRIMARY KEY,
        some_name_ending_in_a_number_1 VARCHAR(255)
    )""",
    """CREATE TABLE IF NOT EXISTS array_table (
        some_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        some_array_1 VARCHAR(255)[],
        some_array_2 VARCHAR(255)[],
        some_jsonb_array JSONB[]
    )""",
    """CREATE TABLE IF NOT EXISTS clazzes_with_getter (
        some_string VARCHAR(255) PRIMARY KEY,
        test_getter VARCHAR
    )""",
]


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def postgres_container():
    container = PostgresContainer()
    await container.start()
    yield container
    await container.stop()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine(postgres_container: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    config = postgres_container.get_connection_config()
    eng = create_async_engine(config.sqlalchemy_url(), echo=False)

    async with eng.begin() as conn:
        for ddl in _CREATE_TABLES:
            await conn.execute(text(ddl))

    yield eng  # type: ignore[misc]
    await eng.dispose()
