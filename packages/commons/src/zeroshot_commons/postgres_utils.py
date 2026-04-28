from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeVar

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

T = TypeVar("T")
UNIQUE_VIOLATION_CODE = "23505"
FOREIGN_KEY_VIOLATION_CODE = "23503"
DETAIL_PATTERN = re.compile(r"Key \((?P<fields>[^)]+)\)=")


class SqlalchemyErrors(StrEnum):
    UNIQUE_CONSTRAINT = UNIQUE_VIOLATION_CODE
    FOREIGN_KEY_CONSTRAINT = FOREIGN_KEY_VIOLATION_CODE


@dataclass(frozen=True, slots=True)
class EntityAlreadyExistsError(RuntimeError):
    fields: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        return f"Entity already exists: {dict(self.fields or {})}"


def _sqlstate(error: BaseException) -> str | None:
    return getattr(getattr(error, "orig", None), "sqlstate", None) or getattr(
        getattr(error, "orig", None), "pgcode", None
    )


def _extract_constraint_fields(error: IntegrityError) -> dict[str, Any]:
    orig = getattr(error, "orig", None)
    diag = getattr(orig, "diag", None)
    detail = getattr(diag, "message_detail", None) or str(orig or "")
    match = DETAIL_PATTERN.search(detail)
    if not match:
        return {}
    field_names = [field.strip() for field in match.group("fields").split(",")]
    return {field_name: None for field_name in field_names}


def _is_unique_violation(error: IntegrityError) -> bool:
    sqlstate = _sqlstate(error)
    if sqlstate == UNIQUE_VIOLATION_CODE:
        return True
    return "unique" in type(getattr(error, "orig", None)).__name__.lower()


async def with_recovery[T](
    supplier: Callable[[], Awaitable[T]],
    errors: AbstractSet[SqlalchemyErrors | str],
) -> None:
    normalized_errors = {
        error.value if isinstance(error, SqlalchemyErrors) else str(error) for error in errors
    }
    try:
        await supplier()
    except SQLAlchemyError as error:
        error_code = _sqlstate(error) or type(error).__name__
        if error_code in normalized_errors:
            return
        raise


async def with_already_exists[T](
    supplier: Callable[[], Awaitable[T]],
) -> T:
    try:
        return await supplier()
    except IntegrityError as error:
        if _is_unique_violation(error):
            raise EntityAlreadyExistsError(_extract_constraint_fields(error)) from error
        raise


async def handle_idempotency[T](
    base_error: SQLAlchemyError,
    recovery_runnable: Callable[[], Awaitable[T]],
    recoverable_constraint_violations: AbstractSet[str] | None = None,
) -> T:
    recoverable = set(recoverable_constraint_violations or {"idempotency_key"})
    if isinstance(base_error, IntegrityError) and _is_unique_violation(base_error):
        fields = _extract_constraint_fields(base_error)
        if recoverable.intersection(fields):
            try:
                return await recovery_runnable()
            except Exception as error:
                raise RuntimeError(f"Failed to recover idempotency violation: {error}") from error
        raise EntityAlreadyExistsError(fields) from base_error
    raise base_error
