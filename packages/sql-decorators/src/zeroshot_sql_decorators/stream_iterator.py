from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from .param_mapper import expand_in_clauses
from .query import BatchingOptions, apply_batching
from .result_mapper import to_instance


class StreamIterator[T]:
    """Lazily streams query results in batches, yielding one row at a time."""

    def __init__(
        self,
        engine: AsyncEngine,
        sql: str,
        replacements: dict[str, Any],
        clazz: type[T] | None = None,
        batch_size: int = 1000,
    ) -> None:
        self._engine = engine
        self._sql = sql
        self._replacements = replacements
        self._clazz = clazz
        self._batch_size = batch_size

    async def _generate(self) -> AsyncIterator[T]:
        offset = 0
        while True:
            batching = BatchingOptions(limit=self._batch_size, offset=offset)
            batch_sql = apply_batching(self._sql, batching)
            expanded_sql, expanded_params = expand_in_clauses(batch_sql, self._replacements)

            async with self._engine.connect() as conn:
                result = await conn.execute(text(expanded_sql), expanded_params)
                rows = result.mappings().all()

            for row in rows:
                instance = to_instance(dict(row), self._clazz)
                yield instance

            if len(rows) < self._batch_size:
                break

            offset += self._batch_size

    def __aiter__(self) -> AsyncIterator[T]:
        return self._generate()
