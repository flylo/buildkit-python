from __future__ import annotations

from dataclasses import dataclass

from zeroshot_openai_utils import ChatResponse, Prompt


def test_prompt_builds_chat_request() -> None:
    prompt = Prompt.for_values("system", "hello", model="gpt-4o-mini", temperature=0.7)
    assert prompt.to_chat_request() == {
        "model": "gpt-4o-mini",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "hello"},
        ],
    }


def test_prompt_omits_temperature_for_gpt5() -> None:
    prompt = Prompt("system", "hello", model="gpt-5")
    assert prompt.to_chat_request()["temperature"] is None


def test_chat_response_extracts_content_from_dicts_and_objects() -> None:
    dict_response = {"choices": [{"message": {"content": "from-dict"}}]}
    assert ChatResponse.for_completion(dict_response).completion == "from-dict"

    @dataclass
    class Message:
        content: str

    @dataclass
    class Choice:
        message: Message

    @dataclass
    class Completion:
        choices: list[Choice]

    object_response = Completion(choices=[Choice(message=Message(content="from-object"))])
    assert ChatResponse.for_completion(object_response).completion == "from-object"


def test_chat_response_for_exception_is_empty() -> None:
    assert ChatResponse.for_exception().completion is None
