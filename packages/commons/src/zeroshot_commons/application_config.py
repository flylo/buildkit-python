from __future__ import annotations

from dataclasses import dataclass

from .config_utils import load_config


@dataclass(slots=True)
class ApplicationConfig:
    local: bool = False
    port: int = 0
    application_root: str | None = None
    use_remote_secrets: bool = False

    @classmethod
    def from_root(cls, application_root: str) -> ApplicationConfig:
        config: dict[str, object] = load_config(application_root)
        return cls(
            local=bool(config.get("local", False)),
            port=int(config.get("port", 0)),
            application_root=application_root,
            use_remote_secrets=bool(config.get("useRemoteSecrets", False)),
        )

    @classmethod
    def create(
        cls,
        local: bool,
        port: int,
        application_root: str | None = None,
    ) -> ApplicationConfig:
        return cls(local=local, port=port, application_root=application_root)
