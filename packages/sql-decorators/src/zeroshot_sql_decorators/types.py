from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any


class QueryType(enum.Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UPSERT = "UPSERT"
    BULK_UPDATE = "BULK_UPDATE"
    BULK_DELETE = "BULK_DELETE"
    RAW = "RAW"


@dataclass(frozen=True, slots=True)
class BooleanResult:
    result: bool


@dataclass(frozen=True, slots=True)
class StringResult:
    result: str


@dataclass(frozen=True, slots=True)
class NumberResult:
    result: int | float


@dataclass(frozen=True, slots=True)
class ArrayResult:
    result: list[str]


type Clazz[T] = type[T]


@dataclass(frozen=True)
class QueryOptions:
    query_type: QueryType
    clazz: type[Any] | None = None
    return_list: bool = False
    query: str | None = None
    file: str | None = None


@dataclass(frozen=True)
class StreamSelectOptions:
    clazz: type[Any] | None = None
    batch_size: int = 1000
    query: str | None = None
    file: str | None = None
