from __future__ import annotations

from .agent_service import AiAgentConfig, AiAgentProvider, AiAgentService, AiAgentServiceLocal
from .service_openai import AiAgentServiceOpenai
from .service_openai_compat import AiAgentServiceOpenAICompat


class AiAgentFactory:
    """Creates the appropriate AiAgentService based on configuration."""

    def __init__(self, config: AiAgentConfig) -> None:
        self._config = config

    def make_agent_service(self) -> AiAgentService:
        if self._config.local:
            return AiAgentServiceLocal.get_instance()

        if self._config.provider == AiAgentProvider.OPENAI_COMPAT:
            if not self._config.openai_compat_base_url:
                raise ValueError(
                    "openai_compat_base_url is required for the OpenAI-compatible provider"
                )
            return AiAgentServiceOpenAICompat(
                base_url=self._config.openai_compat_base_url,
                api_key=self._config.openai_compat_api_key or "",
                default_model=self._config.default_model or "",
            )

        if self._config.provider == AiAgentProvider.OPENAI:
            if not self._config.openai_api_token:
                raise ValueError("openai_api_token is required for the OpenAI provider")
            return AiAgentServiceOpenai(
                api_key=self._config.openai_api_token,
                default_model=self._config.default_model or "gpt-4o",
            )

        raise ValueError(f"Unknown provider: {self._config.provider}")

    @staticmethod
    def make_openai_compat_service(
        base_url: str,
        api_key: str,
        default_model: str,
    ) -> AiAgentServiceOpenAICompat:
        return AiAgentServiceOpenAICompat(
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
        )

    @staticmethod
    def make_openai_service(
        api_key: str,
        default_model: str = "gpt-4o",
    ) -> AiAgentServiceOpenai:
        return AiAgentServiceOpenai(api_key=api_key, default_model=default_model)
