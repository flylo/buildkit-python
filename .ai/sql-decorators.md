# sql-decorators Framework

We have a custom in-house framework for interacting with the SQL database. It allows us to use actual SQL queries.
The logic lives in `packages/sql-decorators`. **100% of DML must use this `sql-decorators` construct.** The queries
should all live in a DAO.

The framework uses SQLAlchemy `text()` with asyncpg to execute raw SQL queries.

## Implementation Details

For implementation details, look at `packages/sql-decorators/src/zeroshot_sql_decorators/decorators.py`. This is where
the main decorators live that translate Python methods on the DAO into actual SQL calls. It also handles parameterized
replacements and IN-clause expansion.

For examples of how to use each decorator, look in `packages/sql-decorators/tests/integration/daos/`.

## Data Access Objects (DAOs)

A DAO encapsulates all interaction with a data source behind a clean interface. DAOs handle queries, inserts, updates,
deletes, and data-mapping so the rest of the application never deals directly with SQL or database drivers.

In a well-structured backend, services depend on DAOs rather than on raw database primitives.

## DAO Structure

```python
from zeroshot_sql_decorators import DaoBase, QueryOptions, QueryType, dao, sql_query

@dao(query_directory=Path(__file__).parent / "queries")
class NoteDao(DaoBase):
    @sql_query(options=QueryOptions(
        query_type=QueryType.SELECT,
        clazz=NoteModel,
        return_list=True,
        query="""
            SELECT * FROM notes
            WHERE (:note_ids IS NULL OR id IN (:note_ids))
              AND (:customer_ids IS NULL OR customer_id IN (:customer_ids))
        """,
    ))
    async def get_notes(
        self, note_ids: list[str] | None = None, customer_ids: list[str] | None = None
    ) -> list[NoteModel]: ...
```

DAOs take an `AsyncEngine` in their constructor (via `DaoBase.__init__`).

## Transactions

When you need to perform multiple inserts, mutations, or anything that requires a SQL transaction, use the
`@sql_transaction` decorator. This creates an `AsyncSession` that must be passed into each method that is part of
the same transaction:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from zeroshot_sql_decorators import TransactionalityBase, sql_transaction, with_transactionality

@with_transactionality()
class NoteRepository(TransactionalityBase):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
        self.note_dao = NoteDao(engine)
        self.audit_dao = AuditDao(engine)

    @sql_transaction()
    async def create_note_with_audit(
        self, note: Note, session: AsyncSession | None = None
    ) -> None:
        await self.note_dao.insert_note(note, session=session)
        await self.audit_dao.log_action("create_note", note.id, session=session)
```

Look in `packages/sql-decorators/tests/integration/daos/test_repository.py` for examples.

## Streaming with @stream_select

The `@stream_select` decorator handles paginating through a database table for large result sets:

```python
@stream_select(options=StreamSelectOptions(
    clazz=TreatmentModel,
    batch_size=1000,
    query="SELECT * FROM treatments WHERE created_at > :created_since ORDER BY created_at",
))
def stream_treatments(self, created_since: int | None = None):
    ...  # Implementation injected by decorator
```

### How stream_select Works

- **Batching**: Executes the SQL query multiple times with `LIMIT` and `OFFSET` clauses.
- **Lazy Fetching**: Fetches the first `batch_size` records, then auto-fetches the next batch when consumed.
- **Termination**: Stops when a batch returns fewer records than `batch_size`.
- **Async Iteration**: Use `async for item in dao.stream_treatments(...):`

### CRITICAL: Sort Order

Because `stream_select` relies on `LIMIT` and `OFFSET`, **the underlying SQL query MUST have a deterministic `ORDER BY`
clause.** Without it, records may be duplicated or skipped between batches.

**Always use a unique, immutable column (like `created_at`) in your `ORDER BY` clause for streaming.**

## PostgreSQL Cast Syntax

When using SQLAlchemy `text()` with asyncpg, avoid the `::type` cast syntax (e.g., `:id::uuid`). asyncpg interprets
`::` as two bind parameters. Use `CAST(:id AS uuid)` instead.
