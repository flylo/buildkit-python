# Configuration

## Configuration Loading

Configuration is read via `packages/commons/src/zeroshot_commons/config_utils.py`. This defaults to reading from a
YAML file at the application root (e.g., `assets/config.yaml`).

Overrides can be set as environment variables with the `app_` prefix:

```
app_remoteClient___port=8080
app_remoteClient___address=localhost
```

### Type Suffixes

Env vars are parsed as strings. For typed values, use suffixes:
- `_numeric`: `app_defaultTokenExpirySeconds_numeric=600` → `600` (int)
- `_boolean`: `app_someFeatureEnabled_boolean=true` → `True` (bool)

## Configuration Classes

Configuration classes are frozen dataclasses with factory methods:

```python
from dataclasses import dataclass
from zeroshot_commons import ApplicationConfig, load_config

@dataclass(frozen=True, slots=True)
class MyServiceConfig:
    api_url: str
    timeout_seconds: int = 30

    CONFIG_KEY = "myService"

    @classmethod
    def from_application_config(cls, app_config: ApplicationConfig) -> "MyServiceConfig":
        data = load_config(app_config.application_root, cls.CONFIG_KEY)
        return cls(
            api_url=str(data["apiUrl"]),
            timeout_seconds=int(data.get("timeoutSeconds", 30)),
        )
```

## Dependency Injection Containers

Configuration flows into DI containers via `dependency-injector`:

```python
from dependency_injector import containers, providers

class MyServiceContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    service_config = providers.Factory(MyServiceConfig.from_mapping, data=config)
    service = providers.Factory(MyService, config=service_config)
```

The container's `config` is populated from the YAML file at runtime.
