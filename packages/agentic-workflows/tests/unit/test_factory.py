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

    def test_static_ollama_factory(self) -> None:
        from zeroshot_agentic_workflows.service_ollama import AiAgentServiceOllama

        service = AiAgentFactory.make_ollama_service()
        assert isinstance(service, AiAgentServiceOllama)


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
