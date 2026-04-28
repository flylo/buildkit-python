from __future__ import annotations

from zeroshot_commons import (
    find_unsafe_string_paths,
    is_image_url,
    is_optional_value,
    is_safe_json,
    is_safe_string,
    value_or_default,
    value_or_default_provider,
)


def test_safe_string_and_json_helpers_match_current_rules() -> None:
    assert is_safe_string("plain text") is True
    assert is_safe_string("visit https://example.com") is False
    assert is_safe_string("<a href='https://example.com'>x</a>") is False

    safe, paths = is_safe_json({"a": ["ok", {"b": "www.example.com"}]})
    assert safe is False
    assert paths == ["a[1].b"]
    assert find_unsafe_string_paths({"body": "[click](https://example.com)"}) == ["body"]


def test_is_image_url_and_default_helpers() -> None:
    assert is_image_url("https://cdn.example.com/file.png", "example.com") is True
    assert is_image_url("https://cdn.other.com/file.png", "example.com") is False
    assert is_image_url("https://cdn.example.com/file.txt", "example.com") is False
    assert value_or_default("", "fallback") == "fallback"
    assert value_or_default_provider(0, lambda: 42) == 42
    assert is_optional_value("hello") is True
    assert is_optional_value("") is False
