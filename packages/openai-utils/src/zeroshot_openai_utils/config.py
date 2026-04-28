from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from zeroshot_commons import ApplicationConfig, load_config


@dataclass(frozen=True, slots=True)
class OpenaiClientConfig:
    api_token: str

    OPENAI_CONFIG_KEY = "openai"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> OpenaiClientConfig:
        return cls(api_token=str(data["apiToken"]))

    @classmethod
    def from_application_config(cls, application_config: ApplicationConfig) -> OpenaiClientConfig:
        if not application_config.application_root:
            raise ValueError("application_root is required to load openai config")
        config: dict[str, Any] = load_config(
            application_config.application_root,
            cls.OPENAI_CONFIG_KEY,
        )
        return cls.from_mapping(config)
