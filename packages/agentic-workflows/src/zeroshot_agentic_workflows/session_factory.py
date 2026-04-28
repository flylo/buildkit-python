from __future__ import annotations

from .session import ConversationSessionRepository, RepositorySession


class AiSessionFactory:
    """Creates or retrieves RepositorySession instances."""

    def __init__(self, repository: ConversationSessionRepository) -> None:
        self._repository = repository

    async def get_or_create_session(
        self,
        client_id: str,
        session_id: str | None = None,
    ) -> RepositorySession:
        if session_id is not None:
            await self._repository.get_session(session_id)
            return RepositorySession(session_id, self._repository)

        session = await self._repository.create_session(client_id)
        return RepositorySession(session.session_id, self._repository)
