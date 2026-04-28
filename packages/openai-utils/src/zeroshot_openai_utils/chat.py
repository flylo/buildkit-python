from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _get_field(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


@dataclass(frozen=True, slots=True)
class Prompt:
    system_prompt: str
    message: str
    model: str = "gpt-4o"
    temperature: float = 0.8

    @classmethod
    def for_values(
        cls,
        system_prompt: str,
        message: str,
        model: str | None = None,
        temperature: float | None = None,
    ) -> Prompt:
        return cls(
            system_prompt=system_prompt,
            message=message,
            model=model or "gpt-4o",
            temperature=0.8 if temperature is None else temperature,
        )

    def to_chat_request(
        self,
        model: str | None = None,
        temperature: float = 0,
    ) -> dict[str, Any]:
        selected_model = model or self.model
        return {
            "model": selected_model,
            "temperature": None if selected_model == "gpt-5" else temperature,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.message},
            ],
        }


@dataclass(frozen=True, slots=True)
class ChatResponse:
    completion: str | None

    @classmethod
    def for_completion(cls, completion: Any) -> ChatResponse:
        choices = _get_field(completion, "choices") or []
        first_choice = choices[0] if choices else None
        message = _get_field(first_choice, "message") if first_choice is not None else None
        content = _get_field(message, "content") if message is not None else None
        return cls(completion=content)

    @classmethod
    def for_exception(cls) -> ChatResponse:
        return cls(completion=None)
