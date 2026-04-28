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
class BrokenType:
    some_string: str


@dao()
class BrokenDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="INSERT INTO broken (some_string) VALUES (:some_string)",
        )
    )
    async def insert_broken_type(self, broken_type: BrokenType) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
        )
    )
    async def no_file_or_query_reference(self, lol: str) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            query="""
                UPDATE broken
                SET some_number = :new_number
                WHERE some_string = :lookup_string
            """,
        )
    )
    async def incorrect_parameter_mapping(
        self, new_number: float, lookup_string: str
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            query="SELECT * FROM broken",
        )
    )
    async def list_needed_without_setting_list_return(self) -> list[BrokenType]: ...
