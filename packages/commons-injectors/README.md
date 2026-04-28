# zeroshot-commons-injectors

Dependency Injector containers for Zeroshot infrastructure components.

This package exposes `dependency-injector` containers for Redis and Postgres
resources so consuming microservices can compose them into an application-level
container without binding directly to a web framework.

Example:

```python
from dependency_injector import containers, providers
from zeroshot_commons_injectors import CommonsInfrastructureContainer


class AppContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    infrastructure = providers.Container(
        CommonsInfrastructureContainer,
        config=config.infrastructure,
    )
```
