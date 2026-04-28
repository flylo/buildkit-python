from __future__ import annotations

import asyncio
import hashlib

import pytest
from zeroshot_commons import (
    CloseableResource,
    Closer,
    djb2_hash,
    get_or_else,
    hash_string,
    is_ip_in_cidr_block,
    is_valid_ip_address,
    is_valid_ip_cidr_block,
    object_to_map,
    parse_ip_address_from_x_forwarded_for,
    random_bytes,
    sha256,
    time_function,
    with_timeout,
)


@pytest.mark.asyncio
async def test_crypto_helpers_match_sha256_and_hex_lengths() -> None:
    expected = hashlib.sha256(b"hello").hexdigest()
    assert await hash_string("hello") == expected
    assert sha256("hello") == expected
    assert len(random_bytes(8)) == 16
    assert djb2_hash("hello") == 261238937


@pytest.mark.asyncio
async def test_get_or_else_preserves_truthy_values_and_recomputes_falsy_values() -> None:
    hits = 0

    async def provider() -> int:
        nonlocal hits
        hits += 1
        return 99

    assert await get_or_else("x", {"x": 7}, provider) == 7
    assert hits == 0

    assert await get_or_else("x", {"x": 0}, provider) == 99
    assert hits == 1


def test_ip_helpers_match_current_typescript_behavior() -> None:
    assert parse_ip_address_from_x_forwarded_for("1.2.3.4, 5.6.7.8") == "1.2.3.4"
    assert parse_ip_address_from_x_forwarded_for("invalid") is None
    assert is_valid_ip_address("127.0.0.1") is True
    assert is_valid_ip_address("999.0.0.1") is False
    assert is_valid_ip_cidr_block("10.0.0.0/8") is True
    assert is_valid_ip_cidr_block("10.0.0.1/8") is True
    assert is_valid_ip_cidr_block("10.0.0.0/33") is False
    assert is_ip_in_cidr_block("10.1.2.3", "10.0.0.0/8") is True
    assert is_ip_in_cidr_block("192.168.1.1", "10.0.0.0/8") is False
    assert is_ip_in_cidr_block("192.168.1.1", "0.0.0.0/0") is True


def test_object_to_map_returns_a_plain_dict_copy() -> None:
    obj = {"a": 1, "b": "two"}
    assert object_to_map(obj) == obj
    assert object_to_map(obj) is not obj


@pytest.mark.asyncio
async def test_time_function_returns_result() -> None:
    async def work() -> str:
        return "done"

    assert await time_function(work, "work") == "done"


@pytest.mark.asyncio
async def test_with_timeout_returns_or_times_out() -> None:
    assert await with_timeout(asyncio.sleep(0, result="ok"), 0.1) == "ok"
    with pytest.raises(TimeoutError):
        await with_timeout(asyncio.sleep(0.05, result="slow"), 0.001)


@pytest.mark.asyncio
async def test_closer_runs_close_hooks_and_swallows_exceptions() -> None:
    closed: list[str] = []

    class Resource:
        pass

    async def close_ok(resource: Resource) -> None:
        closed.append(type(resource).__name__)

    async def close_broken(resource: Resource) -> None:
        closed.append(f"{type(resource).__name__}:broken")
        raise RuntimeError("boom")

    closer = Closer.create(
        CloseableResource(Resource(), close_ok),
        CloseableResource(Resource(), close_broken),
    )

    await closer.close()
    assert closed == ["Resource", "Resource:broken"]
