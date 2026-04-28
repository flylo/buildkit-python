from __future__ import annotations

import hashlib
import secrets


async def hash_string(input_value: str) -> str:
    return hashlib.sha256(input_value.encode("utf-8")).hexdigest()


def sha256(input_value: str) -> str:
    return hashlib.sha256(input_value.encode("utf-8")).hexdigest()


def random_bytes(byte_size: int) -> str:
    return secrets.token_hex(byte_size)


def djb2_hash(value: str) -> int:
    hash_value = 5381
    for char in value:
        hash_value = ((hash_value << 5) + hash_value + ord(char)) & 0xFFFFFFFF
        if hash_value >= 0x80000000:
            hash_value -= 0x100000000
    return hash_value
