from __future__ import annotations

import socket

from zeroshot_commons import (
    PortConfig,
    from_iso_string,
    get_day_of_month,
    kebab_to_camel,
    not_empty,
    random_int,
    remove_props,
    to_iso_string,
)


def test_not_empty_matches_current_semantics() -> None:
    assert not not_empty(None)
    assert not not_empty(0)
    assert not not_empty("")
    assert not not_empty("unknown")
    assert not not_empty("SOME_UNKNOWN_VALUE")
    assert not_empty(False)
    assert not_empty("hello")
    assert not_empty(1)


def test_remove_props_removes_nested_keys_up_to_default_depth() -> None:
    obj = {
        "id": "root",
        "secret": "x",
        "child": {
            "visible": True,
            "secret": "y",
            "items": [
                {"secret": "z", "name": "one"},
                {"name": "two"},
            ],
        },
    }

    assert remove_props(obj, "secret") == {
        "id": "root",
        "child": {
            "visible": True,
            "items": [
                {"name": "one"},
                {"name": "two"},
            ],
        },
    }


def test_kebab_to_camel_converts_each_segment() -> None:
    assert kebab_to_camel("hello-world-test") == "helloWorldTest"


def test_random_int_is_inclusive() -> None:
    values = {random_int(3, 3) for _ in range(5)}
    assert values == {3}


def test_iso_helpers_round_trip() -> None:
    timestamp_ms = 1_700_000_000_123
    assert to_iso_string(timestamp_ms) == "2023-11-14T22:13:20.123Z"
    assert from_iso_string("2023-11-14T22:13:20.123Z") == timestamp_ms
    assert get_day_of_month(timestamp_ms) == 14


async def test_find_open_port_returns_a_port() -> None:
    from zeroshot_commons import find_open_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    found = await find_open_port(PortConfig(min_port=port, max_port=port))
    assert found == port
