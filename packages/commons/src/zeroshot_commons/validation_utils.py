from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

HTML_TAG_PATTERN = re.compile(r"</?\s*[a-z][\s\S]*?>", re.IGNORECASE)
SCRIPT_STYLE_PATTERN = re.compile(r"<(script|style)\b[\s\S]*?>[\s\S]*?</\1>", re.IGNORECASE)
URL_PATTERN = re.compile(r"(http://|https://|www\.)", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\([^)]+\)")
HREF_ATTRIBUTE_PATTERN = re.compile(r"""\bhref\s*=\s*(['"])?[^'"\s>]+\1?""", re.IGNORECASE)
MALICIOUS_LINK_PATTERN = re.compile(
    r"(<a\s+|</a>|href=|src=|http://|https://|www\.|[^<]\[[^\]]+\]\([^)]+\))",
    re.IGNORECASE,
)
VALID_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg")


def is_safe_string(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    return not (
        HTML_TAG_PATTERN.search(value)
        or SCRIPT_STYLE_PATTERN.search(value)
        or URL_PATTERN.search(value)
        or MARKDOWN_LINK_PATTERN.search(value)
        or HREF_ATTRIBUTE_PATTERN.search(value)
    )


def find_unsafe_string_paths(obj: Any) -> list[str]:
    unsafe_paths: list[str] = []

    def traverse(current: Any, path: str) -> None:
        if current is None:
            return
        if isinstance(current, str):
            if MALICIOUS_LINK_PATTERN.search(current):
                unsafe_paths.append(path or "root")
            return
        if isinstance(current, list):
            for index, item in enumerate(current):
                traverse(item, f"{path}[{index}]")
            return
        if isinstance(current, dict):
            for key, value in current.items():
                traverse(value, f"{path}.{key}" if path else str(key))

    traverse(obj, "")
    return unsafe_paths


def is_safe_json(value: Any) -> tuple[bool, list[str]]:
    if not isinstance(value, (dict, list)) or value is None:
        return True, []
    unsafe_paths = find_unsafe_string_paths(value)
    return len(unsafe_paths) == 0, unsafe_paths


def is_image_url(value: Any, host_name_contains: str | list[str]) -> bool:
    if not isinstance(value, str) or not value:
        return True

    try:
        parsed = urlparse(value)
    except ValueError:
        return False

    if not parsed.scheme or not parsed.hostname:
        return False

    if host_name_contains == "":
        host_matches = True
    elif isinstance(host_name_contains, list):
        host_matches = any(host in parsed.hostname for host in host_name_contains)
    else:
        host_matches = host_name_contains in parsed.hostname

    extension_matches = parsed.path.lower().endswith(VALID_IMAGE_EXTENSIONS)
    return host_matches and extension_matches
