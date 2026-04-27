from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run tests marked as integration tests.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if config.getoption("--integration"):
        return

    skip_integration = pytest.mark.skip(reason="Use --integration to run integration tests.")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
