from __future__ import annotations

from dataclasses import dataclass, field

from zeroshot_sql_decorators import (
    DaoBase,
    QueryOptions,
    QueryType,
    dao,
    sql_query,
)


@dataclass
class SubType:
    name: str


@dataclass
class Nested:
    id: str
    some_array_field: list[SubType] | None = field(default=None)


@dao()
class NestedDao(DaoBase):
    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="INSERT INTO nested (id) VALUES (:id)",
        )
    )
    async def insert_nested(self, nested: Nested) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.INSERT,
            query="INSERT INTO sub_type (name) VALUES (:name)",
        )
    )
    async def insert_sub_type(self, sub_type: SubType) -> None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Nested,
            query="""
                SELECT n.id,
                       COALESCE(
                           json_agg(json_build_object('name', st.name))
                           FILTER (WHERE st.name IS NOT NULL),
                           '[]'
                       ) AS some_array_field
                FROM nested n
                LEFT JOIN sub_type st ON true
                WHERE n.id = :id
                GROUP BY n.id
            """,
        )
    )
    async def get_nested(self, id: str) -> Nested | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Nested,
            query="""
                SELECT n.id,
                       COALESCE(
                           json_agg(json_build_object('name', st.name))
                           FILTER (WHERE st.name IS NOT NULL AND st.name = :name),
                           '[]'
                       ) AS some_array_field
                FROM nested n
                LEFT JOIN sub_type st ON true
                WHERE n.id = :id
                GROUP BY n.id
            """,
        )
    )
    async def get_specific_nested(self, id: str, name: str) -> Nested | None: ...

    @sql_query(
        options=QueryOptions(
            query_type=QueryType.SELECT,
            clazz=Nested,
            return_list=True,
            query="""
                SELECT n.id,
                       COALESCE(
                           json_agg(json_build_object('name', st.name))
                           FILTER (WHERE st.name IS NOT NULL),
                           '[]'
                       ) AS some_array_field
                FROM nested n
                LEFT JOIN sub_type st ON true
                GROUP BY n.id
            """,
        )
    )
    async def get_multiple_nesteds(self) -> list[Nested]: ...
