"""Tests for AgentParameterMapper."""

from __future__ import annotations

import json

from zeroshot_agentic_workflows import AgentParameterMapper, RepositorySession


class TestParameterMapper:
    def test_maps_simple_args_to_json(self) -> None:
        def method(self, name: str, age: int) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        result = mapper.map_arguments(("Alice", 30))
        parsed = json.loads(result.input)
        assert parsed == {"name": "Alice", "age": 30}
        assert result.context is None

    def test_extracts_context_param(self) -> None:
        def method(self, query: str, context: dict) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        ctx = {"user_id": "123"}
        result = mapper.map_arguments(("test query", ctx))
        parsed = json.loads(result.input)
        assert "context" not in parsed
        assert parsed == {"query": "test query"}
        assert result.context == ctx

    def test_excludes_repository_session(self) -> None:
        def method(self, text: str, session: RepositorySession) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        # Can't construct a real RepositorySession without a repo, but
        # we can test find_session with a mock
        result = mapper.map_arguments(("hello",))
        parsed = json.loads(result.input)
        assert parsed == {"text": "hello"}

    def test_find_session_returns_session(self) -> None:
        from unittest.mock import MagicMock

        def method(self, text: str, session: RepositorySession) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        mock_session = MagicMock(spec=RepositorySession)
        found = mapper.find_session(("hello", mock_session))
        assert found is mock_session

    def test_find_session_returns_none_when_absent(self) -> None:
        def method(self, text: str) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        assert mapper.find_session(("hello",)) is None

    def test_get_param_value(self) -> None:
        def method(self, x: str, y: int) -> None: ...

        mapper = AgentParameterMapper.from_function(method)
        assert mapper.get_param_value("y", ("a", 42)) == 42
        assert mapper.get_param_value("z", ("a", 42)) is None
