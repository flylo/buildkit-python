from __future__ import annotations

from dataclasses import dataclass

from zeroshot_sql_decorators import (
    DaoBase,
    QueryOptions,
    QueryType,
    dao,
    sql_query,
)


@dataclass
class SomeArrayResult:
    some_id: str
    some_array_1: list[str] | None = None
    some_array_2: list[str] | None = None


@dataclass
class JsonbArrayResult:
    result: list[object] | None = None


@dao()
class ArrayDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            clazz=SomeArrayResult,
            query="""
                INSERT INTO array_table (some_array_1)
                VALUES (COALESCE(:some_array_1, CAST(ARRAY[] AS VARCHAR[])))
                RETURNING *
            """,
        )
    )
    async def insert_array1(self, some_array_1: list[str]) -> SomeArrayResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=SomeArrayResult,
            return_list=True,
            query="""
                SELECT * FROM array_table
                WHERE some_array_1 @> CAST(ARRAY[:tag] AS VARCHAR[])
            """,
        )
    )
    async def find_array1_by_tag(self, tag: str) -> list[SomeArrayResult]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=SomeArrayResult,
            query="SELECT some_id, some_array_1 FROM array_table WHERE some_id = CAST(:id AS uuid)",
        )
    )
    async def find_array1_by_id(self, id: str) -> SomeArrayResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=SomeArrayResult,
            query="SELECT some_id, some_array_2 FROM array_table WHERE some_id = CAST(:id AS uuid)",
        )
    )
    async def find_array2_by_id(self, id: str) -> SomeArrayResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=SomeArrayResult,
            query="""
                UPDATE array_table
                SET some_array_1 = array_cat(some_array_1, CAST(:new_tags AS VARCHAR[]))
                WHERE some_id = CAST(:id AS uuid)
                RETURNING *
            """,
        )
    )
    async def concat_array1(self, id: str, new_tags: list[str]) -> SomeArrayResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=SomeArrayResult,
            query="""
                UPDATE array_table
                SET some_array_1 = COALESCE(:some_array_1, CAST(ARRAY[] AS VARCHAR[]))
                WHERE some_id = CAST(:id AS uuid)
                RETURNING *
            """,
        )
    )
    async def overwrite_array1(
        self, id: str, some_array_1: list[str]
    ) -> SomeArrayResult | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO array_table (some_jsonb_array)
                VALUES (CAST(:json_array_string AS JSONB[]))
                RETURNING *
            """,
        )
    )
    async def insert_jsonb_array(self, json_array_string: str) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=JsonbArrayResult,
            query="""
                SELECT some_jsonb_array as result
                FROM array_table
                WHERE some_id = CAST(:id AS uuid)
            """,
        )
    )
    async def find_jsonb_array_by_id(self, id: str) -> JsonbArrayResult | None: ...
