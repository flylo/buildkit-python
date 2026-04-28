from __future__ import annotations

import json

import pytest

from zeroshot_agentic_workflows import (
    AgentConfig,
    AgentRunConfig,
    AiAgentServiceLocal,
    InMemoryConversationSessionRepository,
    RepositorySession,
)


@pytest.fixture(autouse=True)
def reset_local_agent_service() -> None:
    AiAgentServiceLocal.clear_all_overrides()


@pytest.mark.asyncio
async def test_local_agent_service_returns_mocked_string_response() -> None:
    service = AiAgentServiceLocal.get_instance()
    config = AgentConfig[str](name="TestStringAgent", instructions="returns strings")
    AiAgentServiceLocal.set_response("TestStringAgent", "This is a test response")

    result = await service.create_and_run(config, AgentRunConfig(input="Test input"))

    assert result.success is True
    assert result.output == "This is a test response"
    assert result.error is None


@pytest.mark.asyncio
async def test_local_agent_service_returns_mocked_structured_response() -> None:
    service = AiAgentServiceLocal.get_instance()
    config = AgentConfig[dict[str, list[str]]](
        name="TestAgent:extractLinks",
        instructions="extract links",
        output_schema=object(),
    )
    AiAgentServiceLocal.set_response(
        "TestAgent:extractLinks",
        {"links": ["https://example.com/page1", "https://example.com/page2"]},
    )

    result = await service.create_and_run(config, AgentRunConfig(input="Extract links"))

    assert result.success is True
    assert result.output == {
        "links": ["https://example.com/page1", "https://example.com/page2"],
    }


@pytest.mark.asyncio
async def test_local_agent_service_returns_responses_in_order_and_repeats_last() -> None:
    service = AiAgentServiceLocal.get_instance()
    config = AgentConfig[str](name="LoopAgent", instructions="loop")
    AiAgentServiceLocal.set_responses("LoopAgent", ["one", "two"])

    result1 = await service.create_and_run(config, AgentRunConfig(input="1"))
    result2 = await service.create_and_run(config, AgentRunConfig(input="2"))
    result3 = await service.create_and_run(config, AgentRunConfig(input="3"))

    assert [result1.output, result2.output, result3.output] == ["one", "two", "two"]


@pytest.mark.asyncio
async def test_local_agent_service_prioritizes_errors() -> None:
    service = AiAgentServiceLocal.get_instance()
    config = AgentConfig[str](name="FailingAgent", instructions="fails")
    AiAgentServiceLocal.set_response("FailingAgent", "ignored")
    AiAgentServiceLocal.set_error("FailingAgent", "Error takes priority")

    result = await service.create_and_run(config, AgentRunConfig(input="Test"))

    assert result.success is False
    assert result.error == "Error takes priority"
    assert result.output is None


@pytest.mark.asyncio
async def test_local_agent_service_supports_two_step_create_and_run() -> None:
    service = AiAgentServiceLocal.get_instance()
    config = AgentConfig[str](name="TwoStepAgent", instructions="test")
    AiAgentServiceLocal.set_response("TwoStepAgent", "Two-step response")

    agent = service.create_agent(config)
    result = await service.run_agent(agent, AgentRunConfig(input="Test"))

    assert result.success is True
    assert result.output == "Two-step response"


@pytest.mark.asyncio
async def test_local_agent_service_writes_chat_turns_into_session() -> None:
    service = AiAgentServiceLocal.get_instance()
    repository = InMemoryConversationSessionRepository()
    backing_session = await repository.create_session("client-1")
    session = RepositorySession(backing_session.session_id, repository)
    config = AgentConfig[dict[str, list[str]]](
        name="SessionAgent",
        instructions="test",
        output_schema=object(),
    )
    AiAgentServiceLocal.set_response("SessionAgent", {"links": ["a", "b"]})

    result = await service.create_and_run(
        config,
        AgentRunConfig(input="Extract links", session=session),
    )

    assert result.success is True
    stored_items = await repository.get_conversation_items(backing_session.session_id)
    assert [item.role for item in stored_items] == ["user", "assistant"]
    assert stored_items[0].content == "Extract links"
    assert stored_items[1].content == json.dumps(
        [{"type": "output_text", "text": json.dumps({"links": ["a", "b"]})}]
    )


@pytest.mark.asyncio
async def test_local_agent_service_uses_defaults_and_mock_working_dir() -> None:
    service = AiAgentServiceLocal.get_instance()
    AiAgentServiceLocal.set_mock_working_dir("/tmp/mock-agent")

    string_result = await service.create_and_run(
        AgentConfig[str](name="UnmockedStringAgent", instructions="test"),
        AgentRunConfig(input="Test"),
    )
    structured_result = await service.create_and_run(
        AgentConfig[dict[str, object]](
            name="UnmockedStructuredAgent",
            instructions="test",
            output_schema=object(),
        ),
        AgentRunConfig(input="Test"),
    )

    assert string_result.output == "Mock response for UnmockedStringAgent"
    assert string_result.working_dir == "/tmp/mock-agent"
    assert structured_result.output == {}
    assert structured_result.working_dir == "/tmp/mock-agent"
