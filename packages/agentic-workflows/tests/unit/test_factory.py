"""Tests for AiAgentFactory and AiSessionFactory."""

from __future__ import annotations

import pytest
from zeroshot_agentic_workflows import (
    AiAgentConfig,
    AiAgentFactory,
    AiAgentProvider,
    AiAgentServiceLocal,
    AiSessionFactory,
    InMemoryConversationSessionRepository,
)


class TestAiAgentFactory:
    def test_local_mode_returns_local_service(self) -> None:
        config = AiAgentConfig(local=True)
        factory = AiAgentFactory(config)
        service = factory.make_agent_service()
        assert isinstance(service, AiAgentServiceLocal)

    def test_openai_provider_requires_token(self) -> None:
        config = AiAgentConfig(
            local=False,
            provider=AiAgentProvider.OPENAI,
        )
        factory = AiAgentFactory(config)
        with pytest.raises(ValueError, match="openai_api_token"):
            factory.make_agent_service()

    def test_static_openai_compat_factory(self) -> None:
        from zeroshot_agentic_workflows.service_openai_compat import AiAgentServiceOpenAICompat

        service = AiAgentFactory.make_openai_compat_service(
            base_url="http://localhost:11434/v1",
            api_key="test",
            default_model="qwen2.5:14b",
        )
        assert isinstance(service, AiAgentServiceOpenAICompat)

    def test_openai_compat_provider_requires_base_url(self) -> None:
        config = AiAgentConfig(
            local=False,
            provider=AiAgentProvider.OPENAI_COMPAT,
        )
        factory = AiAgentFactory(config)
        with pytest.raises(ValueError, match="openai_compat_base_url"):
            factory.make_agent_service()


class TestAiSessionFactory:
    async def test_creates_new_session(self) -> None:
        repo = InMemoryConversationSessionRepository()
        factory = AiSessionFactory(repo)

        session = await factory.get_or_create_session("client-1")
        assert session.session_id is not None

    async def test_retrieves_existing_session(self) -> None:
        repo = InMemoryConversationSessionRepository()
        factory = AiSessionFactory(repo)

        created = await repo.create_session("client-1")
        retrieved = await factory.get_or_create_session("client-1", session_id=created.session_id)
        assert retrieved.session_id == created.session_id
