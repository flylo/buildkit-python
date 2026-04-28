from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_query_cache: dict[str, str] = {}


@dataclass(frozen=True, slots=True)
class BatchingOptions:
    limit: int
    offset: int


def load_query(
    *,
    inline_query: str | None,
    file_path: str | None,
    query_directory: Path | None,
    class_name: str,
    method_name: str,
) -> str:
    cache_key = f"{class_name}.{method_name}"
    cached = _query_cache.get(cache_key)
    if cached is not None:
        return cached

    if inline_query is not None:
        _query_cache[cache_key] = inline_query
        return inline_query

    if file_path is not None:
        resolved = Path(file_path)
        if not resolved.is_absolute() and query_directory is not None:
            resolved = query_directory / file_path
    elif query_directory is not None:
        resolved = query_directory / f"{method_name}.sql"
    else:
        raise ValueError(
            f"{class_name}.{method_name}: no query, file, or query_directory specified"
        )

    if not resolved.exists():
        raise FileNotFoundError(
            f"{class_name}.{method_name}: SQL file not found: {resolved}"
        )

    sql = resolved.read_text()
    _query_cache[cache_key] = sql
    return sql


def apply_batching(sql: str, batching: BatchingOptions | None) -> str:
    if batching is None:
        return sql
    return f"{sql.rstrip().rstrip(';')}\nLIMIT {batching.limit} OFFSET {batching.offset}"
