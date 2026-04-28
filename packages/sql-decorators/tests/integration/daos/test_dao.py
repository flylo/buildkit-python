from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zeroshot_sql_decorators import (
    BooleanResult,
    DaoBase,
    NumberResult,
    QueryOptions,
    QueryType,
    StreamSelectOptions,
    StringResult,
    dao,
    sql_query,
    stream_select,
)

QUERY_DIR = Path(__file__).parent


@dataclass
class Thing:
    some_string: str
    some_number: float
    some_int: int


@dao(query_directory=QUERY_DIR)
class TestDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            file="insert_query.sql",
        )
    )
    async def insert_query(self, some_string: str, some_number: float, some_int: int) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Thing,
            query="SELECT * FROM test WHERE some_string = :some_string",
        )
    )
    async def select_query(self, some_string: str) -> Thing | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=Thing,
            file="some_folder/update_query.sql",
        )
    )
    async def update_query(self, new_number: float, search_string: str) -> Thing | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=Thing,
            return_list=True,
            query="""
                UPDATE test
                SET some_int = :new_int
                WHERE some_string IN (:search_string1, :search_string2)
                RETURNING *
            """,
        )
    )
    async def update_multiple_things_query(
        self, new_int: int, search_string1: str, search_string2: str
    ) -> list[Thing]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.BULK_UPDATE,
            query="""
                UPDATE test
                SET some_int = :new_int
                WHERE some_string IN (:search_string1, :search_string2)
            """,
        )
    )
    async def bulk_update_multiple_things_query(
        self, new_int: int, search_string1: str, search_string2: str
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.BULK_DELETE,
            query="""
                DELETE FROM test
                WHERE some_string IN (:search_string1, :search_string2)
            """,
        )
    )
    async def delete_multiple_things_query(
        self, search_string1: str, search_string2: str
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.DELETE,
            query="DELETE FROM test WHERE some_string = :some_string",
        )
    )
    async def delete_query(self, some_string: str) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPSERT,
            query="""
                INSERT INTO test (some_string, some_number, some_int)
                VALUES (:some_string, :some_number, :some_int)
                ON CONFLICT (some_string) DO UPDATE SET
                    some_number = EXCLUDED.some_number,
                    some_int = EXCLUDED.some_int
            """,
        )
    )
    async def upsert_query(self, thing: Thing) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            clazz=Thing,
            query="""
                INSERT INTO test (some_string, some_number, some_int)
                VALUES (:some_string, :some_number, :some_int)
                ON CONFLICT (some_string) DO UPDATE SET
                    some_number = EXCLUDED.some_number,
                    some_int = EXCLUDED.some_int
                RETURNING *
            """,
        )
    )
    async def upsert_query_with_return(
        self, some_string: str, some_number: float, some_int: int
    ) -> Thing | None: ...

    @stream_select(
        options=StreamSelectOptions(
            clazz=Thing,
            batch_size=2,
            query="SELECT * FROM test WHERE some_int >= :min_int AND some_int <= :max_int",
        )
    )
    def iterator(self, min_int: int, max_int: int) -> None: ...  # type: ignore[return]

    @stream_select(
        options=StreamSelectOptions(
            clazz=Thing,
            batch_size=2,
            file="stream_things.sql",
        )
    )
    def stream_things(self, min_int: int, max_int: int) -> None: ...  # type: ignore[return]

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=BooleanResult,
            query="SELECT true as result",
        )
    )
    async def boolean_result(self) -> BooleanResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=StringResult,
            query="SELECT 'lol' as result",
        )
    )
    async def string_result(self) -> StringResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=NumberResult,
            query="SELECT 1 as result",
        )
    )
    async def number_result(self) -> NumberResult | None: ...
