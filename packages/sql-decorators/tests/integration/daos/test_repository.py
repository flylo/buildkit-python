from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from zeroshot_sql_decorators import (
    TransactionalityBase,
    sql_transaction,
    with_transactionality,
)

from .enum_dao import EnumDao, EnumRecord
from .lol_dao import Lol, LolDao


@with_transactionality()
class TestRepository(TransactionalityBase):
    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__(engine)
        self.lol_dao = LolDao(engine)
        self.enum_dao = EnumDao(engine)

    @sql_transaction()
    async def insert_lols_and_enums_in_transaction(
        self,
        lol_record: Lol,
        enum_record: EnumRecord,
        session: AsyncSession | None = None,
    ) -> None:
        await self.lol_dao.insert_lol_transactionally(lol_record, session=session)
        await self.enum_dao.insert_enum_record_transactionally(enum_record, session=session)

    @sql_transaction(isolation_level="SERIALIZABLE")
    async def nested_transaction(self, session: AsyncSession | None = None) -> None:
        pass

    @sql_transaction()
    async def trigger_rollback(
        self,
        lol_record: Lol,
        session: AsyncSession | None = None,
    ) -> None:
        await self.lol_dao.insert_lol_transactionally(lol_record, session=session)
        raise RuntimeError("Intentional error to trigger rollback")
