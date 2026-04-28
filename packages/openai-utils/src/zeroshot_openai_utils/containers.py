from __future__ import annotations

from dependency_injector import containers, providers

from .config import OpenaiClientConfig
from .factory import OpenaiClientFactory
from .service import OpenaiService


def _make_service(factory: OpenaiClientFactory) -> OpenaiService:
    return factory.make_openai_service()


class OpenaiContainer(containers.DeclarativeContainer):
    """Dependency-injector container for OpenAI client wiring.

    Config shape::

        {
            "local": false,
            "apiToken": "sk-..."
        }
    """

    config = providers.Configuration()

    client_config = providers.Factory(
        OpenaiClientConfig.from_mapping,
        data=config,
    )

    factory = providers.Factory(
        OpenaiClientFactory,
        local=config.local,
        config=client_config,
    )

    service = providers.Factory(
        _make_service,
        factory=factory,
    )
