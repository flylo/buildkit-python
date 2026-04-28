"""SQL-focused decorators and helpers for Zeroshot Python packages."""

from .decorators import (
    DaoBase,
    TransactionalityBase,
    dao,
    sql_query,
    sql_transaction,
    stream_select,
    with_transactionality,
)
from .stream_iterator import StreamIterator
from .types import (
    ArrayResult,
    BooleanResult,
    NumberResult,
    QueryOptions,
    QueryType,
    StreamSelectOptions,
    StringResult,
)

__all__ = [
    "ArrayResult",
    "BooleanResult",
    "DaoBase",
    "NumberResult",
    "QueryOptions",
    "QueryType",
    "StreamIterator",
    "StreamSelectOptions",
    "StringResult",
    "TransactionalityBase",
    "dao",
    "sql_query",
    "sql_transaction",
    "stream_select",
    "with_transactionality",
]
