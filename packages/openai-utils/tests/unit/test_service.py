"""Port of the TS openai-client.spec.ts test suite."""

from __future__ import annotations

import json

import pytest
from zeroshot_openai_utils import OpenaiServiceLocal, Prompt


@pytest.fixture(autouse=True)
def _reset_local_service() -> None:
    OpenaiServiceLocal.clear_errors()
    OpenaiServiceLocal.clear_responses()


def _make_service() -> OpenaiServiceLocal:
    return OpenaiServiceLocal.get_instance()


async def test_generate_chat_response() -> None:
    service = _make_service()
    prompt = Prompt.for_values(
        system_prompt="You are a chatbot",
        message="Hello!",
    )
    response = await service.chat_completion(prompt)
    assert response.completion is not None
    assert len(response.completion) > 0


async def test_return_none_on_error() -> None:
    OpenaiServiceLocal.set_error("chatbot", 1)
    service = _make_service()

    prompt = Prompt.for_values(
        system_prompt="You are a chatbot",
        message="Hello!",
    )

    response1 = await service.chat_completion(prompt)
    assert response1.completion is None

    response2 = await service.chat_completion(prompt)
    assert response2.completion is not None


async def test_return_json_when_asked() -> None:
    sample_json = json.dumps(
        {
            "questions": [
                {"question": "What?", "category": "general"},
                {"question": "Why?", "category": "philosophy"},
            ]
        }
    )
    OpenaiServiceLocal.set_response("json", sample_json)
    service = _make_service()

    prompt = Prompt.for_values(
        system_prompt="Give me json plz",
        message="Denver, CO",
    )

    response = await service.chat_completion(prompt)
    assert response.completion is not None
    parsed = json.loads(response.completion)
    assert len(parsed["questions"]) == 2


async def test_error_n_times_then_respond() -> None:
    OpenaiServiceLocal.set_error("json", 3)
    OpenaiServiceLocal.set_response("json", '{"result": true}')
    service = _make_service()

    prompt = Prompt.for_values(
        system_prompt="Give me json",
        message="test",
    )

    for _ in range(3):
        r = await service.chat_completion(prompt)
        assert r.completion is None

    r4 = await service.chat_completion(prompt)
    assert r4.completion is not None
