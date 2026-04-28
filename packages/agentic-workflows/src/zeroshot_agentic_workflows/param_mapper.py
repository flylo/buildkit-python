from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any

from .session import RepositorySession


@dataclass
class MappedArguments:
    input: str
    context: dict[str, Any] | None = None


class AgentParameterMapper:
    """Maps decorated method parameters to agent input JSON."""

    def __init__(self, param_names: list[str]) -> None:
        self._param_names = param_names

    @classmethod
    def from_function(cls, func: Any) -> AgentParameterMapper:
        sig = inspect.signature(func)
        names = [
            name
            for name, _param in sig.parameters.items()
            if name != "self"
        ]
        return cls(names)

    def map_arguments(self, args: tuple[Any, ...]) -> MappedArguments:
        input_obj: dict[str, Any] = {}
        context: dict[str, Any] | None = None

        for name, value in zip(self._param_names, args):
            if isinstance(value, RepositorySession):
                continue
            if name == "context":
                context = value
                continue
            input_obj[name] = value

        return MappedArguments(
            input=json.dumps(input_obj, indent=2, default=str),
            context=context,
        )

    def find_session(self, args: tuple[Any, ...]) -> RepositorySession | None:
        for value in args:
            if isinstance(value, RepositorySession):
                return value
        return None

    def get_param_value(self, name: str, args: tuple[Any, ...]) -> Any:
        for pname, value in zip(self._param_names, args):
            if pname == name:
                return value
        return None
