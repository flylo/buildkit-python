# Testing

## Test Categories

Tests are organized into three tiers, each gated by a CLI flag:

| Tier | Directory | Flag | What it tests |
|------|-----------|------|---------------|
| Unit | `tests/unit/` | *(always runs)* | Pure logic, no I/O |
| Integration | `tests/integration/` | `--integration` | Real Postgres/Redis via testcontainers |
| Eval | `tests/evals/` | `--eval` | Real LLM inference via Ollama |

Run them:
```bash
uv run pytest                  # unit only
uv run pytest --integration    # unit + integration
uv run pytest --eval           # unit + eval
make test-integration          # shortcut
make test-eval                 # shortcut
```

## Integration Tests

Integration tests use testcontainers to boot real dependencies (Postgres, Redis) and validate packages end-to-end.

Test structure:
- Boot dependencies via testcontainers
- Create an `AsyncEngine` from the container's connection config
- Create tables and run assertions against the real database

## Unit Tests

We use unit tests for testing smaller units of code. If we ever create a utility function, especially one that lives in
a common place (like `commons`), then we must have unit tests.

A good example: `packages/commons/tests/unit/test_utils.py`.

## Testcontainers

`packages/commons-testing` provides testcontainer utilities for spinning up real Postgres and Redis instances in tests:

```python
from zeroshot_commons_testing import PostgresContainer, RedisContainer

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def postgres_container():
    container = PostgresContainer()
    await container.start()
    yield container
    await container.stop()

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def engine(postgres_container):
    config = postgres_container.get_connection_config()
    eng = create_async_engine(config.sqlalchemy_url())
    async with eng.begin() as conn:
        await conn.execute(text("CREATE TABLE ..."))
    yield eng
    await eng.dispose()
```

These containers provide `PostgresConnectionConfig` and `RedisConnectionConfig` objects from `zeroshot-commons`.

## Overriding Configuration in Tests

Override configuration by injecting values directly into DI containers:

```python
from zeroshot_commons_injectors import PostgresConnectionContainer

container = PostgresConnectionContainer()
container.config.from_dict({
    "host": postgres_container.get_connection_config().host,
    "port": postgres_container.get_connection_config().port,
    ...
})
```

Or bypass DI entirely and construct services directly with test values.

## Third-Party API Mocking

Third-party `*-utils` packages have local implementations for testing. The local implementation exposes class methods
so tests can change or access mock state:

```python
from zeroshot_openai_utils import OpenaiServiceLocal

OpenaiServiceLocal.set_response("json", '{"result": true}')
OpenaiServiceLocal.set_error("chatbot", 3)  # fail 3 times then succeed
# ... run test ...
OpenaiServiceLocal.clear_responses()
OpenaiServiceLocal.clear_errors()
```

For agent services:
```python
from zeroshot_agentic_workflows import AiAgentServiceLocal

AiAgentServiceLocal.set_response("MyAgent:classify", {"type": "paystub"})
AiAgentServiceLocal.set_error("MyAgent:extract", "intentional failure")
# ... run test ...
AiAgentServiceLocal.clear_all_overrides()
```
