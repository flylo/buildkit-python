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
class NullableRecord:
    some_id: str
    some_nullable_string: str | None = None
    some_nullable_number: float | None = None


@dao()
class NullableDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO nullable_table (some_id, some_nullable_string, some_nullable_number)
                VALUES (:some_id, :some_nullable_string, :some_nullable_number)
            """,
        )
    )
    async def insert_nullable_record(self, nullable_record: NullableRecord) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=NullableRecord,
            query="SELECT * FROM nullable_table WHERE some_id = :id",
        )
    )
    async def select_nullable_record(self, id: str) -> NullableRecord | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=NullableRecord,
            query="""
                UPDATE nullable_table
                SET some_nullable_string = COALESCE(:some_nullable_string, some_nullable_string),
                    some_nullable_number = COALESCE(:some_nullable_number, some_nullable_number)
                WHERE some_id = :some_id
                RETURNING *
            """,
        )
    )
    async def update_nullable_record(
        self, nullable_record: NullableRecord
    ) -> NullableRecord | None: ...
