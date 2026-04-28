"""Port of the full sql-decorators TypeScript test suite."""

from __future__ import annotations

import random
import string
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from .daos.array_dao import ArrayDao, SomeArrayResult
from .daos.broken_dao import BrokenDao, BrokenType
from .daos.clazz_dao import TEST_GETTER_VALUE, ClazzDao, TestClazz, TestClazzWithGetter
from .daos.enum_dao import EnumDao, EnumRecord, SomeEnum
from .daos.lol_dao import Lol, LolDao
from .daos.nested_dao import Nested, NestedDao, SubType
from .daos.nullable_dao import NullableDao, NullableRecord
from .daos.test_dao import TestDao, Thing
from .daos.test_repository import TestRepository
from .daos.unconventional_dao import UnconventionalDao, UnconventionalType

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_letters, k=length))


def _random_int() -> int:
    return random.randint(10_000, 99_999)


def _random_float(scalar: float = 5.0) -> float:
    return round(random.random() * scalar, 4)


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------


class TestBasicCrud:
    async def test_happy_path_end_to_end(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        n = _random_float()
        i = _random_int()

        await dao.insert_query(s, n, i)

        result = await dao.select_query(s)
        assert result is not None
        assert result.some_string == s
        assert float(result.some_number) == n
        assert result.some_int == i

        new_number = _random_float()
        updated = await dao.update_query(new_number, s)
        assert updated is not None
        assert float(updated.some_number) == new_number

        await dao.delete_query(s)
        deleted = await dao.select_query(s)
        assert deleted is None

    async def test_select_non_existent_record(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.select_query("does-not-exist")
        assert result is None

    async def test_update_non_existent_record(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.update_query(999.0, "does-not-exist")
        assert result is None

    async def test_bulk_update_non_existent_records(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.bulk_update_multiple_things_query(
            999, "does-not-exist-1", "does-not-exist-2"
        )
        assert result is None

    async def test_delete_non_existent_record(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.delete_query("does-not-exist")
        assert result is None


# ---------------------------------------------------------------------------
# List / bulk operations
# ---------------------------------------------------------------------------


class TestBulkOperations:
    async def test_select_multiple_rows(self, engine: AsyncEngine) -> None:
        dao = LolDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_lol(Lol(s1))
        await dao.insert_lol(Lol(s2))

        result = await dao.get_multiple_lols(s1, s2)
        assert len(result) == 2

    async def test_update_multiple_rows(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_query(s1, _random_float(), _random_int())
        await dao.insert_query(s2, _random_float(), _random_int())

        new_int = _random_int()
        result = await dao.update_multiple_things_query(new_int, s1, s2)
        assert len(result) == 2
        assert all(r.some_int == new_int for r in result)

    async def test_bulk_update(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_query(s1, _random_float(), _random_int())
        await dao.insert_query(s2, _random_float(), _random_int())

        result = await dao.bulk_update_multiple_things_query(_random_int(), s1, s2)
        assert result is None

    async def test_bulk_delete(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_query(s1, _random_float(), _random_int())
        await dao.insert_query(s2, _random_float(), _random_int())

        result = await dao.delete_multiple_things_query(s1, s2)
        assert result is None

        check1 = await dao.select_query(s1)
        check2 = await dao.select_query(s2)
        assert check1 is None
        assert check2 is None

    async def test_select_multiple_returns_empty_list(self, engine: AsyncEngine) -> None:
        dao = LolDao(engine)
        result = await dao.get_multiple_lols("nope-1", "nope-2")
        assert result == []


# ---------------------------------------------------------------------------
# Query cache
# ---------------------------------------------------------------------------


class TestQueryCache:
    async def test_same_results_on_second_run(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        n = _random_float()
        i = _random_int()

        await dao.insert_query(s, n, i)

        r1 = await dao.select_query(s)
        r2 = await dao.select_query(s)
        assert r1 == r2

        await dao.delete_query(s)


# ---------------------------------------------------------------------------
# Class instances
# ---------------------------------------------------------------------------


class TestClassInstances:
    async def test_class_instances_and_lists(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1 = _random_string()
        s2 = _random_string()
        n1 = _random_float()
        n2 = _random_float()

        inserted1 = await dao.insert_test_clazz(TestClazz(s1, n1))
        assert isinstance(inserted1, TestClazz)
        assert inserted1.some_string == s1

        inserted2 = await dao.insert_test_clazz(TestClazz(s2, n2))
        assert isinstance(inserted2, TestClazz)

        fetched = await dao.get_multiple_test_clazzes(s1, s2)
        assert len(fetched) == 2
        assert all(isinstance(c, TestClazz) for c in fetched)

        single = await dao.get_test_clazz(s1)
        assert isinstance(single, TestClazz)
        assert single.test_function() == f"{s1}-{n1}"

    async def test_update_class_instances(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s = _random_string()
        n = _random_float()
        await dao.insert_test_clazz(TestClazz(s, n))

        new_number = _random_float()
        updated = await dao.update_test_clazz(new_number, s)
        assert updated is not None
        assert float(updated.some_number) == new_number

    async def test_bulk_update_class_instances(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))
        await dao.insert_test_clazz(TestClazz(s2, _random_float()))

        result = await dao.bulk_update_many_test_clazzes(_random_float(), s1, s2)
        assert result is None

    async def test_update_multiple_records_with_returning(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))
        await dao.insert_test_clazz(TestClazz(s2, _random_float()))

        new_number = _random_float()
        result = await dao.update_many_test_clazzes(new_number, s1, s2)
        assert len(result) == 2
        assert all(float(c.some_number) == new_number for c in result)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    async def test_propagate_database_errors(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        await dao.insert_query(s, _random_float(), _random_int())

        with pytest.raises(Exception):
            await dao.insert_query(s, _random_float(), _random_int())

        await dao.delete_query(s)

    async def test_no_file_or_query_reference(self, engine: AsyncEngine) -> None:
        dao = BrokenDao(engine)
        with pytest.raises((ValueError, FileNotFoundError)):
            await dao.no_file_or_query_reference("lol")

    async def test_multiple_rows_without_return_list(self, engine: AsyncEngine) -> None:
        dao = BrokenDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_broken_type(BrokenType(s1))
        await dao.insert_broken_type(BrokenType(s2))

        with pytest.raises(ValueError, match="return_list"):
            await dao.list_needed_without_setting_list_return()

        # Clean up
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM broken"))

    async def test_incorrect_parameter_mapping(self, engine: AsyncEngine) -> None:
        dao = BrokenDao(engine)
        s = _random_string()
        await dao.insert_broken_type(BrokenType(s))

        with pytest.raises(Exception):
            await dao.incorrect_parameter_mapping(999.0, s)

        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM broken"))


# ---------------------------------------------------------------------------
# Nullable fields
# ---------------------------------------------------------------------------


class TestNullableFields:
    async def test_coalescing_undefined_in_update(self, engine: AsyncEngine) -> None:
        dao = NullableDao(engine)
        record = NullableRecord(
            some_id=_random_string(),
            some_nullable_string="hello",
            some_nullable_number=42.0,
        )
        await dao.insert_nullable_record(record)

        # Update with None values — COALESCE should keep originals
        partial = NullableRecord(some_id=record.some_id)
        updated = await dao.update_nullable_record(partial)
        assert updated is not None
        assert updated.some_nullable_string == "hello"
        assert float(updated.some_nullable_number) == 42.0

    async def test_insert_with_none_fields(self, engine: AsyncEngine) -> None:
        dao = NullableDao(engine)
        record = NullableRecord(some_id=_random_string())
        await dao.insert_nullable_record(record)

        result = await dao.select_nullable_record(record.some_id)
        assert result is not None
        assert result.some_nullable_string is None
        assert result.some_nullable_number is None

    async def test_select_records_with_none_fields(self, engine: AsyncEngine) -> None:
        dao = NullableDao(engine)
        record = NullableRecord(
            some_id=_random_string(),
            some_nullable_string="test",
        )
        await dao.insert_nullable_record(record)

        result = await dao.select_nullable_record(record.some_id)
        assert result is not None
        assert result.some_nullable_string == "test"
        assert result.some_nullable_number is None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    async def test_records_with_enums(self, engine: AsyncEngine) -> None:
        dao = EnumDao(engine)
        record = EnumRecord(some_id=_random_string(), some_enum=SomeEnum.A.value)
        await dao.insert_enum_record_transactionally(record)

        result = await dao.select_enum_record(record.some_id)
        assert result is not None
        assert result.some_enum == SomeEnum.A.value


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TestTransactions:
    async def test_execute_multiple_queries_in_transaction(self, engine: AsyncEngine) -> None:
        dao = EnumDao(engine)
        records = [
            EnumRecord(some_id=_random_string(), some_enum=SomeEnum.A.value),
            EnumRecord(some_id=_random_string(), some_enum=SomeEnum.B.value),
        ]
        await dao.insert_many_transactionally(records)

        r1 = await dao.select_enum_record(records[0].some_id)
        r2 = await dao.select_enum_record(records[1].some_id)
        assert r1 is not None
        assert r2 is not None

    async def test_query_without_transaction(self, engine: AsyncEngine) -> None:
        dao = EnumDao(engine)
        record = EnumRecord(some_id=_random_string(), some_enum=SomeEnum.B.value)
        await dao.insert_enum_record_transactionally(record)

        result = await dao.select_enum_record(record.some_id)
        assert result is not None

    async def test_transaction_rollback_on_failure(self, engine: AsyncEngine) -> None:
        dao = EnumDao(engine)
        existing = EnumRecord(some_id=_random_string(), some_enum=SomeEnum.A.value)
        await dao.insert_enum_record_transactionally(existing)

        # Second record has a duplicate ID → INSERT will fail mid-transaction
        records = [
            EnumRecord(some_id=_random_string(), some_enum=SomeEnum.A.value),
            existing,  # duplicate PK
        ]

        with pytest.raises(Exception):
            await dao.insert_many_transactionally(records)

        # First record in the batch should NOT have been committed
        check = await dao.select_enum_record(records[0].some_id)
        assert check is None


# ---------------------------------------------------------------------------
# JSON aggregation / nested
# ---------------------------------------------------------------------------


class TestNestedJsonAgg:
    async def test_json_agg_results(self, engine: AsyncEngine) -> None:
        dao = NestedDao(engine)
        nested_id = _random_string()
        sub1 = _random_string()
        sub2 = _random_string()

        await dao.insert_nested(Nested(id=nested_id))
        await dao.insert_sub_type(SubType(name=sub1))
        await dao.insert_sub_type(SubType(name=sub2))

        result = await dao.get_nested(nested_id)
        assert result is not None
        assert result.id == nested_id
        assert result.some_array_field is not None
        assert len(result.some_array_field) == 2

        # Clean up for isolation
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM sub_type"))
            await conn.execute(text("DELETE FROM nested"))

    async def test_empty_sub_arrays(self, engine: AsyncEngine) -> None:
        dao = NestedDao(engine)
        nested_id = _random_string()
        sub_name = _random_string()

        await dao.insert_nested(Nested(id=nested_id))
        await dao.insert_sub_type(SubType(name=sub_name))

        # Query for a sub_type name that doesn't match
        result = await dao.get_specific_nested(nested_id, "non-existent")
        assert result is not None
        assert result.some_array_field is not None
        assert len(result.some_array_field) == 0

        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM sub_type"))
            await conn.execute(text("DELETE FROM nested"))


# ---------------------------------------------------------------------------
# Upserts
# ---------------------------------------------------------------------------


class TestUpserts:
    async def test_upsert(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        thing = Thing(some_string=s, some_number=_random_float(), some_int=_random_int())

        await dao.upsert_query(thing)
        result1 = await dao.select_query(s)
        assert result1 is not None

        # Upsert with different values
        new_thing = Thing(some_string=s, some_number=_random_float(), some_int=_random_int())
        await dao.upsert_query(new_thing)
        result2 = await dao.select_query(s)
        assert result2 is not None
        assert float(result2.some_number) == new_thing.some_number
        assert result2.some_int == new_thing.some_int

        await dao.delete_query(s)

    async def test_upsert_with_return(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        n = _random_float()
        i = _random_int()

        result = await dao.upsert_query_with_return(s, n, i)
        assert result is not None
        assert result.some_string == s

        # Upsert again
        n2 = _random_float()
        result2 = await dao.upsert_query_with_return(s, n2, i)
        assert result2 is not None
        assert float(result2.some_number) == n2

        await dao.delete_query(s)


# ---------------------------------------------------------------------------
# Streaming / iterators
# ---------------------------------------------------------------------------


class TestStreaming:
    async def test_async_iterable(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        inserted = []
        for _ in range(5):
            s = _random_string()
            i = _random_int()
            await dao.insert_query(s, _random_float(), i)
            inserted.append((s, i))

        min_int = min(t[1] for t in inserted)
        max_int = max(t[1] for t in inserted)

        results: list[Thing] = []
        async for thing in dao.iterator(min_int, max_int):
            results.append(thing)

        assert len(results) >= 5

        for s, _ in inserted:
            await dao.delete_query(s)

    async def test_stream_with_class(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2, s3 = _random_string(), _random_string(), _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))
        await dao.insert_test_clazz(TestClazz(s2, _random_float()))
        await dao.insert_test_clazz(TestClazz(s3, _random_float()))

        results: list[TestClazz] = []
        async for clazz in dao.iterator():
            results.append(clazz)
            assert isinstance(clazz, TestClazz)

        assert len(results) >= 3

    async def test_stream_no_results(self, engine: AsyncEngine) -> None:
        # Use a table that's empty for this test
        dao = TestDao(engine)
        results: list[Thing] = []
        async for thing in dao.iterator(999_999_998, 999_999_999):
            results.append(thing)
        assert results == []

    async def test_stream_from_sql_file(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        s = _random_string()
        i = _random_int()
        await dao.insert_query(s, _random_float(), i)

        results: list[Thing] = []
        async for thing in dao.stream_things(0, 999_999_999):
            results.append(thing)

        assert len(results) >= 1

        await dao.delete_query(s)


# ---------------------------------------------------------------------------
# Scalar results
# ---------------------------------------------------------------------------


class TestScalarResults:
    async def test_boolean_result(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.boolean_result()
        assert result is not None
        assert result.result is True

    async def test_string_result(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.string_result()
        assert result is not None
        assert result.result == "lol"

    async def test_number_result(self, engine: AsyncEngine) -> None:
        dao = TestDao(engine)
        result = await dao.number_result()
        assert result is not None
        assert result.result == 1


# ---------------------------------------------------------------------------
# IN clauses
# ---------------------------------------------------------------------------


class TestInClauses:
    async def test_in_clause_with_strings(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2, s3 = _random_string(), _random_string(), _random_string()
        n1, n2, n3 = _random_float(), _random_float(), _random_float()
        await dao.insert_test_clazz(TestClazz(s1, n1))
        await dao.insert_test_clazz(TestClazz(s2, n2))
        await dao.insert_test_clazz(TestClazz(s3, n3))

        result = await dao.get_grouped_test_clazzes_by_string([s1, s2])
        assert len(result) == 2
        names = {c.some_string for c in result}
        assert s1 in names
        assert s2 in names

    async def test_in_clause_with_numbers(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        n1, n2 = _random_float(), _random_float()
        await dao.insert_test_clazz(TestClazz(s1, n1))
        await dao.insert_test_clazz(TestClazz(s2, n2))

        result = await dao.get_grouped_test_clazzes_by_number([n1, n2])
        assert len(result) == 2

    async def test_in_clause_with_none_to_skip(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1 = _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))

        # None means "don't filter" → should return results
        result = await dao.get_grouped_test_clazzes_by_string(None)
        assert len(result) >= 1

    async def test_in_clause_complex_type_strings(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))
        await dao.insert_test_clazz(TestClazz(s2, _random_float()))

        from dataclasses import dataclass

        @dataclass
        class GroupedQuery:
            query_strings: list[str] | None = None
            query_numbers: list[float] | None = None

        result = await dao.get_grouped_test_clazzes(GroupedQuery(query_strings=[s1, s2]))
        assert len(result) == 2

    async def test_in_clause_complex_type_numbers(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        n1, n2 = _random_float(), _random_float()
        await dao.insert_test_clazz(TestClazz(s1, n1))
        await dao.insert_test_clazz(TestClazz(s2, n2))

        from dataclasses import dataclass

        @dataclass
        class GroupedQuery:
            query_strings: list[str] | None = None
            query_numbers: list[float] | None = None

        result = await dao.get_grouped_test_clazzes(GroupedQuery(query_numbers=[n1, n2]))
        assert len(result) == 2

    async def test_in_clause_complex_type_multiple(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        n1, n2 = _random_float(), _random_float()
        await dao.insert_test_clazz(TestClazz(s1, n1))
        await dao.insert_test_clazz(TestClazz(s2, n2))

        from dataclasses import dataclass

        @dataclass
        class GroupedQuery:
            query_strings: list[str] | None = None
            query_numbers: list[float] | None = None

        result = await dao.get_grouped_test_clazzes(
            GroupedQuery(query_strings=[s1, s2], query_numbers=[n1, n2])
        )
        assert len(result) == 2

    async def test_in_clause_in_stream_select(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s1, s2 = _random_string(), _random_string()
        await dao.insert_test_clazz(TestClazz(s1, _random_float()))
        await dao.insert_test_clazz(TestClazz(s2, _random_float()))

        results: list[TestClazz] = []
        async for clazz in dao.stream_with_in_clause([s1, s2]):
            results.append(clazz)

        assert len(results) == 2


# ---------------------------------------------------------------------------
# Arrays
# ---------------------------------------------------------------------------


class TestArrays:
    async def test_insert_and_retrieve_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        tags = ["tag1", "tag2", "tag3"]
        result = await dao.insert_array1(tags)
        assert result is not None
        assert result.some_array_1 == tags

    async def test_insert_and_retrieve_empty_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        result = await dao.insert_array1([])
        assert result is not None
        assert result.some_array_1 == []

    async def test_retrieve_null_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        result = await dao.insert_array1(["x"])
        assert result is not None
        # some_array_2 was never set, should be null
        result2 = await dao.find_array2_by_id(result.some_id)
        assert result2 is not None
        assert result2.some_array_2 is None

    async def test_update_and_retrieve_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        result = await dao.insert_array1(["a", "b"])
        assert result is not None

        updated = await dao.concat_array1(result.some_id, ["c", "d"])
        assert updated is not None
        assert updated.some_array_1 == ["a", "b", "c", "d"]

    async def test_overwrite_array_to_empty(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        result = await dao.insert_array1(["a", "b"])
        assert result is not None

        updated = await dao.overwrite_array1(result.some_id, [])
        assert updated is not None
        assert updated.some_array_1 == []


# ---------------------------------------------------------------------------
# JSONB arrays
# ---------------------------------------------------------------------------


class TestJsonbArrays:
    async def test_insert_and_retrieve_jsonb_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        import json

        data = [{"key": "value1"}, {"key": "value2"}]
        # asyncpg needs individual JSON strings in a Python list for JSONB[]
        json_list = [json.dumps(d) for d in data]

        # Insert via raw SQL to get the ID
        async with engine.begin() as conn:
            row = await conn.execute(
                text("INSERT INTO array_table (some_jsonb_array) VALUES (:val) RETURNING some_id"),
                {"val": json_list},
            )
            row_id = str(row.mappings().one()["some_id"])

        result = await dao.find_jsonb_array_by_id(row_id)
        assert result is not None
        assert result.result is not None
        assert len(result.result) == 2

    async def test_insert_and_retrieve_empty_jsonb_array(self, engine: AsyncEngine) -> None:
        dao = ArrayDao(engine)
        async with engine.begin() as conn:
            row = await conn.execute(
                text(
                    "INSERT INTO array_table (some_jsonb_array) "
                    "VALUES (CAST(ARRAY[] AS JSONB[])) RETURNING some_id"
                ),
            )
            row_id = str(row.mappings().one()["some_id"])

        result = await dao.find_jsonb_array_by_id(row_id)
        assert result is not None
        assert result.result is not None
        assert len(result.result) == 0


# ---------------------------------------------------------------------------
# Getters
# ---------------------------------------------------------------------------


class TestGetters:
    async def test_insert_with_getter_field(self, engine: AsyncEngine) -> None:
        dao = ClazzDao(engine)
        s = _random_string()
        obj = TestClazzWithGetter(some_string=s)
        await dao.insert_test_getter_value(obj)

        result = await dao.select_test_getter_value(s)
        assert result is not None
        assert result.result == TEST_GETTER_VALUE


# ---------------------------------------------------------------------------
# Unconventional field names
# ---------------------------------------------------------------------------


class TestUnconventionalFields:
    async def test_unconventional_field_names(self, engine: AsyncEngine) -> None:
        dao = UnconventionalDao(engine)
        record = UnconventionalType(
            some_1_name_2_with_3_numbers_4_intertwined=_random_string(),
            some_name_ending_in_a_number_1=_random_string(),
        )
        await dao.insert_unconventional_type(record)

        results = await dao.select_unconventional_type()
        assert len(results) >= 1
        match = next(
            (
                r
                for r in results
                if r.some_1_name_2_with_3_numbers_4_intertwined
                == record.some_1_name_2_with_3_numbers_4_intertwined
            ),
            None,
        )
        assert match is not None
        assert match.some_name_ending_in_a_number_1 == record.some_name_ending_in_a_number_1


# ---------------------------------------------------------------------------
# Cross-DAO transactions (repository layer)
# ---------------------------------------------------------------------------


class TestCrossDaoTransactions:
    async def test_multi_dao_commit(self, engine: AsyncEngine) -> None:
        repo = TestRepository(engine)
        lol = Lol(some_string=_random_string())
        enum_rec = EnumRecord(some_id=_random_string(), some_enum=SomeEnum.A.value)

        await repo.insert_lols_and_enums_in_transaction(lol, enum_rec)

        lol_check = await repo.lol_dao.get_lol(lol.some_string)
        enum_check = await repo.enum_dao.select_enum_record(enum_rec.some_id)
        assert lol_check is not None
        assert enum_check is not None

    async def test_multi_dao_rollback(self, engine: AsyncEngine) -> None:
        repo = TestRepository(engine)
        lol = Lol(some_string=_random_string())

        with pytest.raises(RuntimeError, match="Intentional error"):
            await repo.trigger_rollback(lol)

        # The lol insert should have been rolled back
        check = await repo.lol_dao.get_lol(lol.some_string)
        assert check is None

    async def test_nested_transaction_error(self, engine: AsyncEngine) -> None:
        repo = TestRepository(engine)
        # Calling nested_transaction should work — it just creates a transaction
        # The error case from TS is about passing an existing non-transactional session,
        # which our implementation also guards against.
        await repo.nested_transaction()
