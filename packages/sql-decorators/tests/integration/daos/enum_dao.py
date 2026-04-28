from __future__ import annotations

import enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from zeroshot_sql_decorators import (
    DaoBase,
    QueryOptions,
    QueryType,
    dao,
    sql_query,
    sql_transaction,
)


class SomeEnum(str, enum.Enum):
    A = "A"
    B = "B"


@dataclass
class EnumRecord:
    some_id: str
    some_enum: str  # stored as string in DB


@dao()
class EnumDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO enum_table (some_id, some_enum)
                VALUES (:some_id, :some_enum)
            """,
        )
    )
    async def insert_enum_record_transactionally(
        self, enum_record: EnumRecord, session: AsyncSession | None = None
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO enum_table (some_id, some_enum)
                VALUES (:some_id, :some_enum)
            """,
        )
    )
    async def insert_enum_by_fields(
        self, some_id: str, some_enum: str, session: AsyncSession | None = None
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=EnumRecord,
            query="SELECT * FROM enum_table WHERE some_id = :id",
        )
    )
    async def select_enum_record(self, id: str) -> EnumRecord | None: ...

    @sql_transaction()
    async def insert_many_transactionally(
        self, enum_records: list[EnumRecord], session: AsyncSession | None = None
    ) -> None:
        for record in enum_records:
            await self.insert_enum_record_transactionally(record, session=session)
