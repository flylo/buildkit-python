from __future__ import annotations

import logging
import secrets
from typing import Protocol

from openai import AsyncOpenAI

from .chat import ChatResponse, Prompt
from .config import OpenaiClientConfig

logger = logging.getLogger(__name__)


class OpenaiService(Protocol):
    async def chat_completion(self, prompt: Prompt) -> ChatResponse: ...


class OpenaiServiceLocal:
    """Mock implementation for testing. Singleton."""

    _instance: OpenaiServiceLocal | None = None
    _responses_by_prompt_substring: dict[str, str] = {}
    _error_counts_by_prompt_substring: dict[str, int] = {}

    @classmethod
    def get_instance(cls) -> OpenaiServiceLocal:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_response(cls, prompt_substring: str, response: str) -> None:
        cls._responses_by_prompt_substring[prompt_substring] = response

    @classmethod
    def set_error(cls, prompt_substring: str, count: int) -> None:
        cls._error_counts_by_prompt_substring[prompt_substring] = count

    @classmethod
    def clear_responses(cls) -> None:
        cls._responses_by_prompt_substring.clear()

    @classmethod
    def clear_errors(cls) -> None:
        cls._error_counts_by_prompt_substring.clear()

    @staticmethod
    def _prompt_text(prompt: Prompt) -> str:
        return f"{prompt.system_prompt} {prompt.message}"

    @classmethod
    def _should_error(cls, prompt: Prompt) -> bool:
        text = cls._prompt_text(prompt)
        for substring, count in list(cls._error_counts_by_prompt_substring.items()):
            if substring in text:
                if count > 0:
                    cls._error_counts_by_prompt_substring[substring] = count - 1
                    return True
                cls._error_counts_by_prompt_substring[substring] = 0
        return False

    @classmethod
    def _response_for_prompt(cls, prompt: Prompt) -> str | None:
        text = cls._prompt_text(prompt)
        for substring, response in cls._responses_by_prompt_substring.items():
            if substring in text:
                return response
        return None

    async def chat_completion(self, prompt: Prompt) -> ChatResponse:
        if self._should_error(prompt):
            return ChatResponse.for_exception()

        keyed = self._response_for_prompt(prompt)
        if keyed is not None:
            return ChatResponse(completion=keyed)

        return ChatResponse(completion=secrets.token_hex(5))


class OpenaiServiceRemote:
    """Real OpenAI API implementation."""

    def __init__(self, config: OpenaiClientConfig) -> None:
        self._client = AsyncOpenAI(api_key=config.api_token)

    async def chat_completion(self, prompt: Prompt) -> ChatResponse:
        try:
            request = prompt.to_chat_request(prompt.model, prompt.temperature)
            response = await self._client.chat.completions.create(**request)
            return ChatResponse.for_completion(response)
        except Exception:
            logger.exception("Error completing chat request")
            return ChatResponse.for_exception()
