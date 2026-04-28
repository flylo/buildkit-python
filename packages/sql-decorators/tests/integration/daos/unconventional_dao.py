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
class UnconventionalType:
    some_1_name_2_with_3_numbers_4_intertwined: str
    some_name_ending_in_a_number_1: str


@dao()
class UnconventionalDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO unconventional (
                    some_1_name_2_with_3_numbers_4_intertwined,
                    some_name_ending_in_a_number_1
                ) VALUES (
                    :some_1_name_2_with_3_numbers_4_intertwined,
                    :some_name_ending_in_a_number_1
                )
            """,
        )
    )
    async def insert_unconventional_type(
        self, unconventional_type: UnconventionalType
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=UnconventionalType,
            return_list=True,
            query="SELECT * FROM unconventional",
        )
    )
    async def select_unconventional_type(self) -> list[UnconventionalType]: ...
