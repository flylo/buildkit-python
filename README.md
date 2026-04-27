# buildkit-python

Python workspace for Zeroshot packages, scaffolded as a multi-package `uv` monorepo.

## Packages

- `zeroshot-commons`
- `zeroshot-commons-testing`
- `zeroshot-agentic-workflows`
- `zeroshot-openai-utils`
- `zeroshot-tavily-utils`
- `zeroshot-docling-utils`
- `zeroshot-sql-decorators`
- `zeroshot-agent-experiments` (private app package)

## Commands

- `make sync`
- `make format`
- `make lint`
- `make typecheck`
- `make test`
- `make test-integration`
- `make build`
- `make build-all`
- `make set-version VERSION=0.1.0`

## Release Flow

1. Run `make set-version VERSION=x.y.z`.
2. Commit the version change.
3. Tag the release with `vx.y.z`.
4. Push the commit and tag.

GitHub Actions will build and publish the public packages with PyPI Trusted Publishing.

Each public PyPI project must be configured with the repository, workflow path, and environment declared in `.github/workflows/publish.yml`.
