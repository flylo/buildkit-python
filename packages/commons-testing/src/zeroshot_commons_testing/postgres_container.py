from __future__ import annotations

import logging
from pathlib import Path

from testcontainers.postgres import PostgresContainer as _PostgresContainer
from zeroshot_commons import PostgresConnectionConfig

logger = logging.getLogger(__name__)

_IMAGE = "postgres:17-alpine"
_USER = "postgres"
_PASSWORD = "password"


class PostgresContainer:
    """Manages a disposable PostgreSQL container for integration tests."""

    def __init__(self, database: str = "postgres") -> None:
        self._database = database
        self._container = _PostgresContainer(
            image=_IMAGE,
            username=_USER,
            password=_PASSWORD,
            dbname=database,
        ).with_bind_ports(5432, 0)
        self._started: _PostgresContainer | None = None

    async def start(self) -> None:
        self._started = self._container.start()

    async def stop(self) -> None:
        if self._started is not None:
            self._started.stop()
            self._started = None

    def get_connection_config(self) -> PostgresConnectionConfig:
        if self._started is None:
            raise RuntimeError("Container has not been started")
        host = self._started.get_container_host_ip()
        port = int(self._started.get_exposed_port(5432))
        return PostgresConnectionConfig(
            host=host,
            port=port,
            username=_USER,
            password=_PASSWORD,
            database=self._database,
        )

    async def apply_migrations(self, migrations_dir: str | Path) -> None:
        """Apply SQL migration files in sorted order."""
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        config = self.get_connection_config()
        engine = create_async_engine(config.sqlalchemy_url())
        migrations_path = Path(migrations_dir)

        files = sorted(f for f in migrations_path.iterdir() if f.is_file() and f.suffix == ".sql")

        async with engine.begin() as conn:
            for f in files:
                sql = f.read_text()
                await conn.execute(text(sql))

        await engine.dispose()
