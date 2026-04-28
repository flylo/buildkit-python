from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from zeroshot_sql_decorators import (
    DaoBase,
    QueryOptions,
    QueryType,
    dao,
    sql_query,
)


@dataclass
class Lol:
    some_string: str


@dao()
class LolDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="INSERT INTO lol (some_string) VALUES (:some_string)",
        )
    )
    async def insert_lol(self, lol: Lol) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="INSERT INTO lol (some_string) VALUES (:some_string)",
        )
    )
    async def insert_lol_transactionally(
        self, lol: Lol, session: AsyncSession | None = None
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Lol,
            query="SELECT * FROM lol WHERE some_string = :query_string",
        )
    )
    async def get_lol(self, query_string: str) -> Lol | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Lol,
            return_list=True,
            query="""
                  SELECT *
                  FROM lol
                  WHERE some_string IN (:query_string1, :query_string2)
                  """,
        )
    )
    async def get_multiple_lols(self, query_string1: str, query_string2: str) -> list[Lol]: ...
