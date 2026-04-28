from __future__ import annotations

from .config import OpenaiClientConfig
from .service import OpenaiService, OpenaiServiceLocal, OpenaiServiceRemote


class OpenaiClientFactory:
    def __init__(self, local: bool, config: OpenaiClientConfig) -> None:
        self._local = local
        self._config = config

    def make_openai_service(self) -> OpenaiService:
        if self._local:
            return OpenaiServiceLocal.get_instance()
        return OpenaiServiceRemote(self._config)
