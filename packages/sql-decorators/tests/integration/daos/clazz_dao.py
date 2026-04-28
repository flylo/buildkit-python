from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from zeroshot_sql_decorators import (
    DaoBase,
    QueryOptions,
    QueryType,
    StreamSelectOptions,
    StringResult,
    dao,
    sql_query,
    stream_select,
)

QUERY_DIR = Path(__file__).parent

TEST_GETTER_VALUE = "testGetter"


@dataclass
class TestClazz:
    some_string: str
    some_number: float

    def test_function(self) -> str:
        return f"{self.some_string}-{self.some_number}"


@dataclass
class TestClazzWithGetter:
    some_string: str

    @property
    def test_getter(self) -> str:
        return TEST_GETTER_VALUE


@dao(query_directory=QUERY_DIR)
class ClazzDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            clazz=TestClazz,
            query="""
                INSERT INTO clazzes (some_string, some_number)
                VALUES (:some_string, :some_number)
                RETURNING *
            """,
        )
    )
    async def insert_test_clazz(self, instance: TestClazz) -> TestClazz | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=TestClazz,
            query="""
                UPDATE clazzes
                SET some_number = :new_number
                WHERE some_string = :lookup_string
                RETURNING *
            """,
        )
    )
    async def update_test_clazz(
        self, new_number: float, lookup_string: str
    ) -> TestClazz | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.UPDATE,
            clazz=TestClazz,
            return_list=True,
            query="""
                UPDATE clazzes
                SET some_number = :new_number
                WHERE some_string IN (:lookup_string1, :lookup_string2)
                RETURNING *
            """,
        )
    )
    async def update_many_test_clazzes(
        self, new_number: float, lookup_string1: str, lookup_string2: str
    ) -> list[TestClazz]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.BULK_UPDATE,
            query="""
                UPDATE clazzes
                SET some_number = :new_number
                WHERE some_string IN (:lookup_string1, :lookup_string2)
            """,
        )
    )
    async def bulk_update_many_test_clazzes(
        self, new_number: float, lookup_string1: str, lookup_string2: str
    ) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=TestClazz,
            query="SELECT * FROM clazzes WHERE some_string = :lookup_string",
        )
    )
    async def get_test_clazz(self, lookup_string: str) -> TestClazz | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=TestClazz,
            return_list=True,
            query="""
                SELECT * FROM clazzes
                WHERE some_string IN (:query_string1, :query_string2)
            """,
        )
    )
    async def get_multiple_test_clazzes(
        self, query_string1: str, query_string2: str
    ) -> list[TestClazz]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=TestClazz,
            return_list=True,
            query="""
                SELECT * FROM clazzes
                WHERE (:query_strings IS NULL OR some_string IN (:query_strings))
            """,
        )
    )
    async def get_grouped_test_clazzes_by_string(
        self, query_strings: list[str] | None = None
    ) -> list[TestClazz]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=TestClazz,
            return_list=True,
            query="""
                SELECT * FROM clazzes
                WHERE some_number IN (:query_numbers)
            """,
        )
    )
    async def get_grouped_test_clazzes_by_number(
        self, query_numbers: list[float]
    ) -> list[TestClazz]: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=TestClazz,
            return_list=True,
            query="""
                SELECT * FROM clazzes
                WHERE (:query_strings IS NULL OR some_string IN (:query_strings))
                  AND (:query_numbers IS NULL OR some_number IN (:query_numbers))
            """,
        )
    )
    async def get_grouped_test_clazzes(self, grouped_query: object) -> list[TestClazz]: ...

    @stream_select(
        options=StreamSelectOptions(
            clazz=TestClazz,
            batch_size=2,
            query="SELECT * FROM clazzes",
        )
    )
    def iterator(self) -> None: ...  # type: ignore[return]

    @stream_select(
        options=StreamSelectOptions(
            clazz=TestClazz,
            batch_size=2,
            query="""
                SELECT * FROM clazzes
                WHERE (:query_strings IS NULL OR some_string IN (:query_strings))
            """,
        )
    )
    def stream_with_in_clause(self, query_strings: list[str]) -> None: ...  # type: ignore[return]

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="""
                INSERT INTO clazzes_with_getter (some_string, test_getter)
                VALUES (:some_string, :test_getter)
            """,
        )
    )
    async def insert_test_getter_value(self, test_clazz: TestClazzWithGetter) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=StringResult,
            query="""
                SELECT test_getter as result
                FROM clazzes_with_getter
                WHERE some_string = :some_string
            """,
        )
    )
    async def select_test_getter_value(self, some_string: str) -> StringResult | None: ...
