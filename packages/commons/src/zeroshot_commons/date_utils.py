from __future__ import annotations

from datetime import UTC, datetime


def get_day_of_month(timestamp_ms: int) -> int:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).day


def to_iso_string(timestamp_ms: int) -> str:
    return (
        datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def from_iso_string(iso_string: str) -> int:
    normalized = iso_string.replace("Z", "+00:00")
    return int(datetime.fromisoformat(normalized).timestamp() * 1000)
