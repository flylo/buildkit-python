# Dependency Injection

All infrastructure wiring uses the `dependency-injector` library with `DeclarativeContainer` classes.

## Container Structure

We create a container for each logical group of functionality:

```python
from dependency_injector import containers, providers

class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    postgres = providers.Container(
        PostgresConnectionContainer,
        config=config.postgres,
    )
    redis = providers.Container(
        RedisConnectionContainer,
        config=config.redis,
    )
```

## Existing Containers

- `zeroshot-commons-injectors` → `RedisConnectionContainer`, `PostgresConnectionContainer`,
  `CommonsInfrastructureContainer`
- `zeroshot-openai-utils` → `OpenaiContainer`

## Provider Types

| Provider | Use for |
|----------|---------|
| `providers.Factory` | New instance each time (configs, services) |
| `providers.Singleton` | Single instance (connection pools) |
| `providers.Resource` | Async lifecycle with init/shutdown (engines, clients) |
| `providers.Container` | Nested sub-container |
| `providers.Configuration` | External config dict/YAML |

## Wiring Pattern

```python
# Create and configure
container = CommonsInfrastructureContainer()
container.config.from_yaml("assets/config.yaml")

# Use
async with container.postgres.engine() as engine:
    ...
```

## Test Overrides

Override any provider for testing:

```python
container = MyContainer()
container.config.from_dict({
    "host": "localhost",
    "port": test_port,
})
```

Or override a specific provider:
```python
container.service.override(providers.Object(mock_service))
```
