from __future__ import annotations

import dataclasses
import inspect
import re
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


def extract_param_names(func: Any) -> list[str]:
    """Get parameter names from a function, excluding ``self`` and ``session``."""
    sig = inspect.signature(func)
    return [
        name
        for name, param in sig.parameters.items()
        if name not in ("self", "session")
        and param.default is not inspect.Parameter.empty
        or param.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY)
        and name not in ("self", "session")
    ]


def _is_complex(value: Any) -> bool:
    """Return True if *value* is a dataclass instance or has a ``__dict__``
    that is not a basic built-in type."""
    if value is None or isinstance(value, (str, int, float, bool, bytes, list, tuple)):
        return False
    return dataclasses.is_dataclass(value) and not isinstance(value, type)


def _extract_fields(obj: Any) -> dict[str, Any]:
    """Pull fields from a dataclass instance, including property getters."""
    result: dict[str, Any] = {}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        for f in dataclasses.fields(obj):
            result[f.name] = getattr(obj, f.name)
        # Also pick up @property descriptors on the class
        for name in dir(type(obj)):
            if name.startswith("_"):
                continue
            attr = getattr(type(obj), name, None)
            if isinstance(attr, property):
                result[name] = attr.fget(obj)  # type: ignore[arg-type]
    return result


def build_replacements(
    param_names: list[str],
    args: tuple[Any, ...],
) -> dict[str, Any]:
    """Map function arguments to SQL ``:param`` replacements.

    Rules (mirroring the TS implementation):
    * Filter out any ``AsyncSession`` values (transaction arg).
    * Single complex arg → spread its fields as parameters.
    * Multiple args → map each name to its value.
    * ``None`` values stay as ``None`` (SQL ``NULL``).
    """
    # Pair up names with values, skip sessions
    pairs: list[tuple[str, Any]] = []
    for name, value in zip(param_names, args):
        if isinstance(value, AsyncSession):
            continue
        pairs.append((name, value))

    if len(pairs) == 1 and _is_complex(pairs[0][1]):
        return _replace_none(_extract_fields(pairs[0][1]))

    replacements: dict[str, Any] = {}
    for name, value in pairs:
        if _is_complex(value):
            replacements.update(_extract_fields(value))
        else:
            replacements[name] = value

    return _replace_none(replacements)


def _replace_none(d: dict[str, Any]) -> dict[str, Any]:
    """Ensure ``None`` values remain as-is (SQLAlchemy handles NULL binding)."""
    return d


# ---------------------------------------------------------------------------
# IN-clause expansion
# ---------------------------------------------------------------------------

_IN_PARAM_RE = re.compile(r":(\w+)")


def _param_is_in_clause(sql: str, key: str) -> bool:
    """Check if ``:key`` appears inside an ``IN (...)`` context in the SQL."""
    pattern = re.compile(rf"IN\s*\([^)]*:{re.escape(key)}(?!\w)[^)]*\)", re.IGNORECASE)
    return pattern.search(sql) is not None


def _param_is_null_check(sql: str, key: str) -> bool:
    """Check if ``:key IS NULL`` appears in the SQL."""
    pattern = re.compile(rf":{re.escape(key)}\s+IS\s+NULL", re.IGNORECASE)
    return pattern.search(sql) is not None


def expand_in_clauses(sql: str, replacements: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Expand list-valued parameters for ``IN (:param)`` clauses.

    Given ``IN (:ids)`` and ``ids=[1, 2, 3]``, rewrites to
    ``IN (:ids_0, :ids_1, :ids_2)`` with individual entries in replacements.

    List parameters that appear outside of IN clauses (e.g. PostgreSQL array
    values) are left as-is.

    Also handles the ``(:param IS NULL OR ... IN (:param))`` pattern.
    """
    expanded: dict[str, Any] = {}
    new_sql = sql

    for key, value in list(replacements.items()):
        has_in = _param_is_in_clause(new_sql, key)
        has_is_null = _param_is_null_check(new_sql, key)

        if value is None and has_is_null:
            # None means "skip this filter"
            _is_null_pat = re.compile(rf":{re.escape(key)}\s+IS\s+NULL", re.IGNORECASE)
            new_sql = _is_null_pat.sub("TRUE", new_sql)
            if has_in:
                _in_pat = re.compile(rf"IN\s*\(\s*:{re.escape(key)}\s*\)", re.IGNORECASE)
                new_sql = _in_pat.sub("IN (NULL)", new_sql)
            continue

        if not isinstance(value, (list, tuple)):
            expanded[key] = value
            continue

        # List value but NOT used in an IN clause — it's a PostgreSQL array param
        if not has_in:
            expanded[key] = value
            continue

        # --- list/tuple in an IN clause ---

        # Handle ":key IS NULL" patterns
        if has_is_null:
            _is_null_pat = re.compile(rf":{re.escape(key)}\s+IS\s+NULL", re.IGNORECASE)
            new_sql = _is_null_pat.sub("FALSE", new_sql)

        if len(value) == 0:
            _in_pat = re.compile(rf"IN\s*\(\s*:{re.escape(key)}\s*\)", re.IGNORECASE)
            new_sql = _in_pat.sub("IN (NULL)", new_sql)
            continue

        # Build individual param names
        param_names = [f"{key}_{i}" for i in range(len(value))]
        placeholders = ", ".join(f":{name}" for name in param_names)

        # Only replace :key references inside IN clauses
        _in_content_pat = re.compile(
            rf"(IN\s*\([^)]*):{re.escape(key)}(?!\w)([^)]*\))", re.IGNORECASE
        )
        new_sql = _in_content_pat.sub(rf"\g<1>{placeholders}\g<2>", new_sql)

        for pname, val in zip(param_names, value):
            expanded[pname] = val

    return new_sql, expanded
