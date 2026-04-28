from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class PromptFrontmatter:
    tools: list[str] = field(default_factory=list)


@dataclass
class ParsedPrompt:
    frontmatter: PromptFrontmatter
    content: str


_FRONTMATTER_RE = re.compile(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$")


def parse_prompt_frontmatter(markdown: str) -> ParsedPrompt:
    match = _FRONTMATTER_RE.match(markdown)
    if not match:
        return ParsedPrompt(frontmatter=PromptFrontmatter(), content=markdown)

    raw_frontmatter = match.group(1)
    content = match.group(2)

    parsed = yaml.safe_load(raw_frontmatter) or {}
    tools = parsed.get("tools", [])

    return ParsedPrompt(
        frontmatter=PromptFrontmatter(tools=tools or []),
        content=content,
    )


def generate_tools_reference(tools: list[Any]) -> str:
    if not tools:
        return ""

    lines = ["## Available Tools\n"]
    for tool in tools:
        name = getattr(tool, "name", str(tool))
        description = getattr(tool, "description", "")
        lines.append(f"### {name}")
        if description:
            lines.append(description)
        lines.append("")

    return "\n".join(lines)


def map_tool_keys(
    tool_keys: list[str],
    registry: dict[str, str],
) -> list[str]:
    mapped: list[str] = []
    for key in tool_keys:
        if key not in registry:
            available = ", ".join(sorted(registry.keys()))
            raise ValueError(f"Tool key '{key}' not found in registry. Available: {available}")
        mapped.append(registry[key])
    return mapped


def validate_tools_match(
    declared_tool_names: list[str],
    actual_tools: list[Any],
) -> None:
    actual_names = {getattr(t, "name", str(t)) for t in actual_tools}
    declared_set = set(declared_tool_names)

    missing = declared_set - actual_names
    extra = actual_names - declared_set

    errors: list[str] = []
    if missing:
        errors.append(f"Declared in frontmatter but not provided: {missing}")
    if extra:
        errors.append(f"Provided but not declared in frontmatter: {extra}")

    if errors:
        raise ValueError("; ".join(errors))
