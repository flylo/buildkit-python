from __future__ import annotations

from zeroshot_commons_injectors import (
    CommonsInfrastructureContainer,
    PostgresConnectionContainer,
    RedisConnectionContainer,
)


def test_container_classes_exist() -> None:
    assert RedisConnectionContainer is not None
    assert PostgresConnectionContainer is not None
    assert CommonsInfrastructureContainer is not None
