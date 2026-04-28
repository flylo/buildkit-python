from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from zeroshot_commons import (
    EntityAlreadyExistsError,
    PostgresConnectionConfig,
    SqlalchemyErrors,
    handle_idempotency,
    with_already_exists,
    with_recovery,
)


class FakeDiag:
    def __init__(self, message_detail: str) -> None:
        self.message_detail = message_detail


class FakeUniqueViolation(Exception):
    def __init__(self, message_detail: str, pgcode: str = "23505") -> None:
        super().__init__(message_detail)
        self.pgcode = pgcode
        self.diag = FakeDiag(message_detail)


class FakeForeignKeyViolation(Exception):
    def __init__(self, pgcode: str = "23503") -> None:
        super().__init__("foreign key violation")
        self.pgcode = pgcode


def make_integrity_error(orig: Exception) -> IntegrityError:
    return IntegrityError("stmt", {}, orig)


@pytest.mark.asyncio
async def test_postgres_error_helpers_match_expected_behavior() -> None:
    recovered = False

    async def raises_fk() -> None:
        raise make_integrity_error(FakeForeignKeyViolation())

    async def raises_unique() -> None:
        raise make_integrity_error(
            FakeUniqueViolation("Key (idempotency_key)=(abc) already exists.")
        )

    async def recovery() -> str:
        nonlocal recovered
        recovered = True
        return "ok"

    await with_recovery(raises_fk, {SqlalchemyErrors.FOREIGN_KEY_CONSTRAINT})

    with pytest.raises(EntityAlreadyExistsError):
        await with_already_exists(raises_unique)

    assert (
        await handle_idempotency(
            make_integrity_error(
                FakeUniqueViolation("Key (idempotency_key)=(abc) already exists.")
            ),
            recovery,
        )
        == "ok"
    )
    assert recovered is True


def test_postgres_connection_config_generates_expected_urls() -> None:
    config = PostgresConnectionConfig.from_mapping(
        {
            "host": "localhost",
            "port": 5432,
            "username": "user",
            "password": "pass",
            "database": "db",
        }
    )

    assert config.url == "postgresql://user:pass@localhost:5432/db"
    assert config.sqlalchemy_url() == "postgresql+asyncpg://user:pass@localhost:5432/db"
