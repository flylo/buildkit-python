from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def not_empty(value: Any) -> bool:
    is_numeric_zero = isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0
    return (
        value is not None
        and not is_numeric_zero
        and value != ""
        and not (isinstance(value, str) and "unknown" in value.lower())
    )


def kebab_to_camel(kebab_case: str) -> str:
    parts = kebab_case.split("-")
    if not parts:
        return kebab_case
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def remove_props(obj: Any, *props: str, max_depth: int = 3) -> Any:
    prop_set = set(props)

    def remove_props_recursive(input_obj: Any, current_depth: int) -> Any:
        if current_depth > max_depth:
            return input_obj

        if isinstance(input_obj, Mapping):
            return {
                key: remove_props_recursive(value, current_depth + 1)
                for key, value in input_obj.items()
                if key not in prop_set
            }

        if isinstance(input_obj, Sequence) and not isinstance(input_obj, (str, bytes, bytearray)):
            return [remove_props_recursive(item, current_depth) for item in input_obj]

        return input_obj

    return remove_props_recursive(obj, 1)
