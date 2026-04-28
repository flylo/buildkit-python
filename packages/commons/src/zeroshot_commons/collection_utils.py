from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import TypeVar


K = TypeVar("K")
V = TypeVar("V")


async def get_or_else(
    key: K,
    mapping: Mapping[K, V],
    if_empty_provider: Callable[[], Awaitable[V]],
) -> V:
    value = mapping.get(key)
    if value:
        return value
    return await if_empty_provider()


def object_to_map(obj: Mapping[str, object]) -> dict[str, object]:
    return dict(obj)
