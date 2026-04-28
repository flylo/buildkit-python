from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .internal_utils import not_empty

T = TypeVar("T")


def value_or_default[T](value: T, default_value: T) -> T:
    return value if not_empty(value) else default_value


def value_or_default_provider[T](value: T, default_provider: Callable[[], T]) -> T:
    return value if not_empty(value) else default_provider()


def is_optional_value(value: object) -> bool:
    return not_empty(value)
