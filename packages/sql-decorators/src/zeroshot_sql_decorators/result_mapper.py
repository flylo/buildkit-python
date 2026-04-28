from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from .types import QueryType


def map_result(
    rows: Sequence[Mapping[str, Any]],
    query_type: QueryType,
    clazz: type[Any] | None,
    return_list: bool,
) -> Any:
    """Map raw database rows to the appropriate return shape."""
    if query_type in (
        QueryType.UPSERT,
        QueryType.DELETE,
        QueryType.BULK_UPDATE,
        QueryType.BULK_DELETE,
        QueryType.RAW,
    ):
        return None

    if query_type == QueryType.SELECT:
        return _map_select(rows, clazz, return_list)

    if query_type in (QueryType.INSERT, QueryType.UPDATE):
        return _map_returning(rows, clazz, return_list)

    return None


def _map_select(
    rows: Sequence[Mapping[str, Any]],
    clazz: type[Any] | None,
    return_list: bool,
) -> Any:
    if return_list:
        return [to_instance(dict(r), clazz) for r in rows]

    if len(rows) == 0:
        return None

    if len(rows) > 1:
        raise ValueError(
            f"Expected 0 or 1 rows but got {len(rows)}. "
            "Set return_list=True in QueryOptions to allow multiple rows."
        )

    return to_instance(dict(rows[0]), clazz)


def _map_returning(
    rows: Sequence[Mapping[str, Any]],
    clazz: type[Any] | None,
    return_list: bool,
) -> Any:
    if len(rows) == 0:
        return None

    if return_list:
        return [to_instance(dict(r), clazz) for r in rows]

    return to_instance(dict(rows[0]), clazz)


def to_instance(row: dict[str, Any], clazz: type[Any] | None) -> Any:
    """Convert a row dict to a class instance or cleaned dict."""
    cleaned = _clean_row(row)

    if clazz is None:
        return cleaned

    if dataclasses.is_dataclass(clazz):
        field_names = {f.name for f in dataclasses.fields(clazz)}
        filtered = {k: v for k, v in cleaned.items() if k in field_names}

        # Handle nested dataclass fields (e.g. from json_agg)
        for f in dataclasses.fields(clazz):
            if f.name in filtered and filtered[f.name] is not None:
                val = filtered[f.name]
                # Check if the field type annotation hints at a list of dataclasses
                origin = getattr(f.type, "__origin__", None)
                if origin is list and isinstance(val, list):
                    args = getattr(f.type, "__args__", ())
                    if args and dataclasses.is_dataclass(args[0]):
                        inner_cls = args[0]
                        filtered[f.name] = [
                            to_instance(item, inner_cls) if isinstance(item, dict) else item
                            for item in val
                        ]

        return clazz(**filtered)

    # Fallback: try to construct the class directly
    return clazz(**cleaned)


def _clean_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise database values: Decimal→float/int, JSON strings→objects."""
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if value is None:
            cleaned[key] = None
        elif isinstance(value, Decimal):
            # Match TS behaviour: NUMERIC → float, BIGINT → int
            if value == int(value):
                cleaned[key] = int(value)
            else:
                cleaned[key] = float(value)
        elif isinstance(value, str) and value.startswith("["):
            try:
                cleaned[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                cleaned[key] = value
        else:
            cleaned[key] = value
    return cleaned
