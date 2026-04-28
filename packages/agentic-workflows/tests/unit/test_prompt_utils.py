"""Tests for prompt_utils and param_mapper."""

from __future__ import annotations

import pytest
from zeroshot_agentic_workflows import (
    generate_tools_reference,
    parse_prompt_frontmatter,
)
from zeroshot_agentic_workflows.prompt_utils import map_tool_keys, validate_tools_match


class TestParsePromptFrontmatter:
    def test_parses_tools_from_frontmatter(self) -> None:
        md = "---\ntools:\n  - search\n  - summarize\n---\nDo the thing."
        parsed = parse_prompt_frontmatter(md)
        assert parsed.frontmatter.tools == ["search", "summarize"]
        assert parsed.content == "Do the thing."

    def test_returns_raw_content_without_frontmatter(self) -> None:
        md = "Just a plain prompt."
        parsed = parse_prompt_frontmatter(md)
        assert parsed.frontmatter.tools == []
        assert parsed.content == "Just a plain prompt."

    def test_handles_empty_frontmatter(self) -> None:
        md = "---\n\n---\nContent here."
        parsed = parse_prompt_frontmatter(md)
        assert parsed.frontmatter.tools == []
        assert parsed.content == "Content here."


class TestGenerateToolsReference:
    def test_returns_empty_for_no_tools(self) -> None:
        assert generate_tools_reference([]) == ""

    def test_generates_reference_section(self) -> None:
        class FakeTool:
            name = "search"
            description = "Search the web"

        ref = generate_tools_reference([FakeTool()])
        assert "### search" in ref
        assert "Search the web" in ref


class TestMapToolKeys:
    def test_maps_keys_through_registry(self) -> None:
        result = map_tool_keys(["s", "w"], {"s": "search", "w": "write"})
        assert result == ["search", "write"]

    def test_raises_for_missing_key(self) -> None:
        with pytest.raises(ValueError, match="not found"):
            map_tool_keys(["missing"], {"s": "search"})


class TestValidateToolsMatch:
    def test_passes_when_matched(self) -> None:
        class T:
            name = "search"

        validate_tools_match(["search"], [T()])

    def test_raises_on_mismatch(self) -> None:
        class T:
            name = "search"

        with pytest.raises(ValueError):
            validate_tools_match(["write"], [T()])
