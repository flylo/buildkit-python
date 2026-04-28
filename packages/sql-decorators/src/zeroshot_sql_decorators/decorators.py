from __future__ import annotations

import functools
import inspect
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .param_mapper import build_replacements, expand_in_clauses, extract_param_names
from .query import load_query
from .result_mapper import map_result
from .stream_iterator import StreamIterator
from .types import QueryOptions, QueryType, StreamSelectOptions

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base classes
# ---------------------------------------------------------------------------


class DaoBase:
    """Base class for Data Access Objects.

    Holds a reference to the SQLAlchemy ``AsyncEngine``.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine


class TransactionalityBase:
    """Base class for repositories that coordinate transactions across DAOs."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine


# ---------------------------------------------------------------------------
# Class decorators
# ---------------------------------------------------------------------------


def dao(*, query_directory: Path | str | None = None) -> Any:
    """Mark a class as a DAO with an optional query file directory."""

    def decorator(cls: type) -> type:
        cls._query_directory = Path(query_directory) if query_directory else None  # type: ignore[attr-defined]
        return cls

    return decorator


def with_transactionality() -> Any:
    """Mark a class as transaction-aware (mirrors TS ``@WithTransactionality()``)."""

    def decorator(cls: type) -> type:
        return cls

    return decorator


# ---------------------------------------------------------------------------
# @sql_query
# ---------------------------------------------------------------------------


def sql_query(options: QueryOptions) -> Any:
    """Method decorator that executes a SQL query and maps the result.

    The decorated method becomes a stub — its body is never called.
    Parameters are extracted from the function signature and bound to the query.
    An optional ``session: AsyncSession | None = None`` parameter enables
    transaction participation.
    """

    def decorator(fn: Any) -> Any:
        param_names = extract_param_names(fn)

        @functools.wraps(fn)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            engine: AsyncEngine = self._engine

            # Resolve query directory
            query_dir: Path | None = getattr(self.__class__, "_query_directory", None)

            sql = load_query(
                inline_query=options.query,
                file_path=options.file,
                query_directory=query_dir,
                class_name=self.__class__.__name__,
                method_name=fn.__name__,
            )

            # Build all args (positional + keyword), excluding self
            all_args = _merge_args(fn, args, kwargs)
            replacements = build_replacements(param_names, all_args)

            # Expand IN clauses for list parameters
            expanded_sql, expanded_params = expand_in_clauses(sql, replacements)

            # Check for an explicit session argument
            session = _extract_session(fn, args, kwargs)

            if session is not None:
                result = await session.execute(text(expanded_sql), expanded_params)
                rows = result.mappings().all() if result.returns_rows else []
            else:
                async with engine.connect() as conn:
                    result = await conn.execute(text(expanded_sql), expanded_params)
                    rows = result.mappings().all() if result.returns_rows else []
                    await conn.commit()

            return map_result(rows, options.query_type, options.clazz, options.return_list)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# @stream_select
# ---------------------------------------------------------------------------


def stream_select(options: StreamSelectOptions) -> Any:
    """Method decorator that returns a ``StreamIterator`` for lazy batch iteration."""

    def decorator(fn: Any) -> Any:
        param_names = extract_param_names(fn)

        @functools.wraps(fn)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> StreamIterator[Any]:
            engine: AsyncEngine = self._engine
            query_dir: Path | None = getattr(self.__class__, "_query_directory", None)

            sql = load_query(
                inline_query=options.query,
                file_path=options.file,
                query_directory=query_dir,
                class_name=self.__class__.__name__,
                method_name=fn.__name__,
            )

            all_args = _merge_args(fn, args, kwargs)
            replacements = build_replacements(param_names, all_args)

            return StreamIterator(
                engine=engine,
                sql=sql,
                replacements=replacements,
                clazz=options.clazz,
                batch_size=options.batch_size,
            )

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# @sql_transaction
# ---------------------------------------------------------------------------


def sql_transaction(
    *,
    isolation_level: str | None = None,
) -> Any:
    """Method decorator that wraps the call in a database transaction.

    If a ``session`` kwarg/arg is already provided and has an active
    transaction, the method participates in that transaction.
    Otherwise a new transaction is created, committed on success,
    and rolled back on error.
    """

    def decorator(fn: Any) -> Any:
        @functools.wraps(fn)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            engine: AsyncEngine = self._engine

            existing_session = _extract_session(fn, args, kwargs)

            if existing_session is not None and existing_session.in_transaction():
                # Already in a transaction — just call through
                return await fn(self, *args, **kwargs)

            if existing_session is not None:
                raise ValueError(
                    "A session was provided but has no active transaction. "
                    "Do not pass a session unless it is already transactional."
                )

            # Create a new session + transaction
            exec_opts: dict[str, Any] = {}
            if isolation_level:
                exec_opts["isolation_level"] = isolation_level

            session_factory = async_sessionmaker(
                engine, expire_on_commit=False,
            )
            async with session_factory.begin() as session:
                if exec_opts:
                    await session.connection(execution_options=exec_opts)
                new_kwargs = dict(kwargs)
                new_kwargs["session"] = session
                return await fn(self, *args, **new_kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _merge_args(fn: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    """Merge positional and keyword args into a positional tuple,
    respecting the original function signature order (excluding ``self``)."""
    sig = inspect.signature(fn)
    params = [p for p in sig.parameters.values() if p.name != "self"]

    merged: list[Any] = list(args)

    # Fill in remaining params from kwargs
    for i in range(len(args), len(params)):
        p = params[i]
        if p.name in kwargs:
            merged.append(kwargs[p.name])
        elif p.default is not inspect.Parameter.empty:
            merged.append(p.default)

    return tuple(merged)


def _extract_session(
    fn: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncSession | None:
    """Pull out the ``session`` argument if present."""
    if "session" in kwargs:
        return kwargs["session"]

    sig = inspect.signature(fn)
    params = [p for p in sig.parameters.values() if p.name != "self"]

    for i, p in enumerate(params):
        if p.name == "session" and i < len(args):
            val = args[i]
            if isinstance(val, AsyncSession):
                return val

    return None
