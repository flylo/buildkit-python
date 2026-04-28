"""OpenAI-compatible utilities for Zeroshot Python packages."""

from .chat import ChatResponse, Prompt
from .config import OpenaiClientConfig
from .containers import OpenaiContainer
from .factory import OpenaiClientFactory
from .service import OpenaiService, OpenaiServiceLocal, OpenaiServiceRemote

__all__ = [
    "ChatResponse",
    "OpenaiClientConfig",
    "OpenaiClientFactory",
    "OpenaiContainer",
    "OpenaiService",
    "OpenaiServiceLocal",
    "OpenaiServiceRemote",
    "Prompt",
]
