from __future__ import annotations

import json

import pytest
from zeroshot_agentic_workflows import (
    InMemoryConversationSessionRepository,
    RepositorySession,
    SessionNotFoundError,
)


@pytest.mark.asyncio
async def test_in_memory_repository_manages_conversation_state() -> None:
    repository = InMemoryConversationSessionRepository()
    session = await repository.create_session("client-1")

    await repository.add_conversation_items(
        session.session_id,
        [
            {"role": "user", "content": "hello", "metadata": {"source": "test"}},
            {"role": "assistant", "content": "world", "metadata": None},
        ],
    )

    items = await repository.get_conversation_items(session.session_id)
    assert [item.sequence_number for item in items] == [0, 1]
    assert items[0].metadata == json.dumps({"source": "test"})
    assert items[1].deleted_at is None

    popped = await repository.pop_last_item(session.session_id)
    assert popped is not None
    assert popped.role == "assistant"

    remaining = await repository.get_conversation_items(session.session_id)
    assert [item.role for item in remaining] == ["user"]

    await repository.clear_conversation(session.session_id)
    assert await repository.get_conversation_items(session.session_id) == []


@pytest.mark.asyncio
async def test_in_memory_repository_raises_for_missing_session() -> None:
    repository = InMemoryConversationSessionRepository()
    with pytest.raises(SessionNotFoundError):
        await repository.get_session("missing")


@pytest.mark.asyncio
async def test_repository_session_down_projects_to_plain_chat_messages() -> None:
    repository = InMemoryConversationSessionRepository()
    backing_session = await repository.create_session("client-1")
    session = RepositorySession(backing_session.session_id, repository)

    await session.add_items(
        [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": [{"type": "output_text", "text": "there"}]},
            {"role": "tool", "content": "ignored"},
        ]
    )

    stored = await repository.get_conversation_items(backing_session.session_id)
    assert [item.role for item in stored] == ["user", "assistant"]
    assert stored[0].content == "hi"
    assert stored[1].content == json.dumps([{"type": "output_text", "text": "there"}])

    items = await session.get_items()
    assert items == [
        {"role": "user", "content": [{"type": "input_text", "text": "hi"}]},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": json.dumps([{"type": "output_text", "text": "there"}]),
                }
            ],
        },
    ]

    popped = await session.pop_item()
    assert popped == {
        "role": "assistant",
        "content": [
            {
                "type": "output_text",
                "text": json.dumps([{"type": "output_text", "text": "there"}]),
            }
        ],
    }
