from __future__ import annotations

import logging
from typing import Any

from agents import Agent, Runner
from agents.model_settings import ModelSettings
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from .agent_service import AgentConfig, AgentRunConfig, AgentRunResult, AgentType, T

logger = logging.getLogger(__name__)


class AiAgentServiceOllama:
    """Ollama implementation via OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        default_model: str = "qwen2.5:14b",
    ) -> None:
        self._base_url = base_url
        self._default_model = default_model
        self._client = AsyncOpenAI(
            base_url=f"{base_url}/v1",
            api_key="ollama",
        )

    def create_agent(self, config: AgentConfig[T]) -> AgentType[T]:
        return AgentType(config=config)

    async def run_agent(
        self,
        agent: AgentType[T],
        config: AgentRunConfig,
    ) -> AgentRunResult[T]:
        return await self.create_and_run(agent.config, config)

    async def create_and_run(
        self,
        agent_config: AgentConfig[T],
        run_config: AgentRunConfig,
    ) -> AgentRunResult[T]:
        try:
            model_name = agent_config.model or self._default_model
            model = OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=self._client,
            )

            ms = agent_config.model_settings
            if ms is not None and not isinstance(ms, ModelSettings):
                ms = ModelSettings(**ms)

            sdk_agent = Agent(
                name=agent_config.name,
                instructions=agent_config.instructions,
                model=model,
                tools=agent_config.tools or [],
                output_type=agent_config.output_schema,
                model_settings=ms or ModelSettings(),
            )

            run_kwargs: dict[str, Any] = {"input": run_config.input}
            if run_config.context is not None:
                run_kwargs["context"] = run_config.context
            if run_config.max_turns is not None:
                run_kwargs["max_turns"] = run_config.max_turns

            result = await Runner.run(sdk_agent, **run_kwargs)

            return AgentRunResult(
                output=result.final_output,
                success=True,
                raw_result=result,
            )
        except Exception as exc:
            error_msg = str(exc)
            if "max_turns" in error_msg.lower():
                logger.warning("Agent %s reached max turns", agent_config.name)
            else:
                logger.exception("Agent %s failed", agent_config.name)
            return AgentRunResult(
                output=None,  # type: ignore[arg-type]
                success=False,
                error=error_msg,
            )
