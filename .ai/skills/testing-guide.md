---
name: testing-guide
description: Reference guide for writing integration, unit, and eval tests
---

Reference guide for writing integration, unit, and eval tests.

Read these docs for full details:
- `.ai/testing.md` for test tiers, testcontainers, and mocking
- `.ai/configuration.md` for config loading and overrides

## Quick Reference

### Test Tiers
- **Unit** (`tests/unit/`): always runs, no I/O
- **Integration** (`tests/integration/`): `--integration` flag, real Postgres/Redis via testcontainers
- **Eval** (`tests/evals/`): `--eval` flag, real LLM inference via Ollama

### Testcontainers
```python
from zeroshot_commons_testing import PostgresContainer, RedisContainer

container = PostgresContainer()
await container.start()
config = container.get_connection_config()  # → PostgresConnectionConfig
```

### Integration Test Fixture Pattern
```python
@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine(postgres_container):
    config = postgres_container.get_connection_config()
    eng = create_async_engine(config.sqlalchemy_url())
    async with eng.begin() as conn:
        await conn.execute(text("CREATE TABLE ..."))
    yield eng
    await eng.dispose()
```

### Mocking AI Services
```python
from zeroshot_agentic_workflows import AiAgentServiceLocal

AiAgentServiceLocal.set_response("AgentName", expected_output)
AiAgentServiceLocal.set_error("AgentName", "error message")
AiAgentServiceLocal.clear_all_overrides()  # in fixture/teardown
```

### Unit Tests
Required for all utility functions, especially in `packages/commons`.

$ARGUMENTS
