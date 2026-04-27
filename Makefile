PUBLIC_PACKAGES := \
	zeroshot-commons \
	zeroshot-commons-testing \
	zeroshot-agentic-workflows \
	zeroshot-openai-utils \
	zeroshot-tavily-utils \
	zeroshot-docling-utils \
	zeroshot-sql-decorators

PRIVATE_PACKAGES := \
	zeroshot-agent-experiments

ALL_PACKAGES := $(PUBLIC_PACKAGES) $(PRIVATE_PACKAGES)

.PHONY: sync format lint typecheck test test-integration build build-all check set-version check-version

sync:
	uv sync --all-packages

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run pyright

test:
	uv run pytest

test-integration:
	uv run pytest --integration

build:
	uv build --package zeroshot-commons --no-sources
	uv build --package zeroshot-commons-testing --no-sources
	uv build --package zeroshot-agentic-workflows --no-sources
	uv build --package zeroshot-openai-utils --no-sources
	uv build --package zeroshot-tavily-utils --no-sources
	uv build --package zeroshot-docling-utils --no-sources
	uv build --package zeroshot-sql-decorators --no-sources

build-all: build
	uv build --package zeroshot-agent-experiments --no-sources

check: lint typecheck test

set-version:
	python3 scripts/workspace.py set-version $(VERSION)

check-version:
	python3 scripts/workspace.py check-version $(VERSION)
