from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
for src_dir in sorted(ROOT.glob("packages/*/src")):
    sys.path.insert(0, str(src_dir))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run tests marked as integration tests.",
    )
    parser.addoption(
        "--eval",
        action="store_true",
        default=False,
        help="Run tests marked as evals (requires a running LLM).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if not config.getoption("--integration"):
        skip_integration = pytest.mark.skip(reason="Use --integration to run integration tests.")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

    if not config.getoption("--eval"):
        skip_eval = pytest.mark.skip(reason="Use --eval to run eval tests (requires a running LLM).")
        for item in items:
            if "eval" in item.keywords:
                item.add_marker(skip_eval)
