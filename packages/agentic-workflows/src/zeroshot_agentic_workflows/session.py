from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from time import time
from typing import Any, Protocol, TypedDict, cast
from uuid import uuid4


CONVERSATION_SESSION_REPOSITORY = "CONVERSATION_SESSION_REPOSITORY"


def _now_ms() -> int:
    return int(time() * 1000)


@dataclass(slots=True)
class ConversationSessionModel:
    session_id: str
    client_id: str
    created_at: int
    updated_at: int


@dataclass(slots=True)
class ConversationItemModel:
    item_id: str
    session_id: str
    sequence_number: int
    role: str
    content: str
    metadata: str | None
    created_at: int
    deleted_at: int | None


class ConversationMessage(TypedDict):
    role: str
    content: str
    metadata: dict[str, Any] | None


class InputTextPart(TypedDict):
    type: str
    text: str


class SessionItem(TypedDict):
    role: str
    content: str | list[InputTextPart]


class ConversationSessionRepository(Protocol):
    async def create_session(self, client_id: str) -> ConversationSessionModel: ...

    async def get_session(self, session_id: str) -> ConversationSessionModel: ...

    async def get_conversation_items(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[ConversationItemModel]: ...

    async def add_conversation_items(
        self,
        session_id: str,
        items: Sequence[ConversationMessage],
    ) -> None: ...

    async def clear_conversation(self, session_id: str) -> None: ...

    async def pop_last_item(self, session_id: str) -> ConversationItemModel | None: ...


class SessionNotFoundError(LookupError):
    pass


class InMemoryConversationSessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSessionModel] = {}
        self._items: dict[str, list[ConversationItemModel]] = {}

    async def create_session(self, client_id: str) -> ConversationSessionModel:
        session_id = str(uuid4())
        now = _now_ms()
        session = ConversationSessionModel(
            session_id=session_id,
            client_id=client_id,
            created_at=now,
            updated_at=now,
        )
        self._sessions[session_id] = session
        self._items[session_id] = []
        return session

    async def get_session(self, session_id: str) -> ConversationSessionModel:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(f"Session not found: {session_id}")
        return session

    async def get_conversation_items(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> list[ConversationItemModel]:
        session_items = self._items.get(session_id, [])
        active_items = [item for item in session_items if item.deleted_at is None]
        if limit:
            return active_items[-limit:]
        return active_items

    async def add_conversation_items(
        self,
        session_id: str,
        items: Sequence[ConversationMessage],
    ) -> None:
        session = await self.get_session(session_id)
        session_items = self._items.get(session_id, [])
        now = _now_ms()
        sequence_number = max((item.sequence_number for item in session_items), default=-1) + 1

        for item in items:
            session_items.append(
                ConversationItemModel(
                    item_id=str(uuid4()),
                    session_id=session_id,
                    sequence_number=sequence_number,
                    role=item["role"],
                    content=item["content"],
                    metadata=(
                        json.dumps(item["metadata"]) if item.get("metadata") is not None else None
                    ),
                    created_at=now,
                    deleted_at=None,
                )
            )
            sequence_number += 1

        self._items[session_id] = session_items
        session.updated_at = now

    async def clear_conversation(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        session_items = self._items.get(session_id, [])
        now = _now_ms()

        for item in session_items:
            if item.deleted_at is None:
                item.deleted_at = now

        session.updated_at = now

    async def pop_last_item(self, session_id: str) -> ConversationItemModel | None:
        session = await self.get_session(session_id)
        session_items = self._items.get(session_id, [])
        active_items = [item for item in session_items if item.deleted_at is None]
        if not active_items:
            return None

        last_item = active_items[-1]
        now = _now_ms()
        last_item.deleted_at = now
        session.updated_at = now
        return last_item


class RepositorySession:
    def __init__(self, session_id: str, repository: ConversationSessionRepository) -> None:
        self.session_id = session_id
        self.repository = repository
        self._cached_items: list[SessionItem] | None = None

    def _to_content_parts(self, role: str, content: str) -> list[InputTextPart]:
        if role == "user":
            return [{"type": "input_text", "text": content}]
        return [{"type": "output_text", "text": content}]

    async def get_items(self, limit: int | None = None) -> list[SessionItem]:
        if limit is None and self._cached_items is not None:
            return self._cached_items

        db_items = await self.repository.get_conversation_items(self.session_id, limit)
        items: list[SessionItem] = [
            SessionItem(
                role=item.role,
                content=self._to_content_parts(item.role, item.content),
            )
            for item in db_items
        ]

        if limit is None:
            self._cached_items = items
        return items

    async def add_items(self, items: Sequence[Mapping[str, Any]]) -> None:
        messages: list[ConversationMessage] = []
        for item in items:
            role = item.get("role")
            if role not in {"user", "assistant", "system"} or "content" not in item:
                continue
            content = item["content"]
            if isinstance(content, str):
                serialized_content = content
            else:
                serialized_content = json.dumps(content)
            messages.append(
                ConversationMessage(
                    role=cast(str, role),
                    content=serialized_content,
                    metadata=None,
                )
            )

        if messages:
            await self.repository.add_conversation_items(self.session_id, messages)
        self._cached_items = None

    async def clear_session(self) -> None:
        await self.repository.clear_conversation(self.session_id)
        self._cached_items = None

    async def pop_item(self) -> SessionItem | None:
        popped_item = await self.repository.pop_last_item(self.session_id)
        self._cached_items = None
        if popped_item is None:
            return None
        return SessionItem(
            role=popped_item.role,
            content=self._to_content_parts(popped_item.role, popped_item.content),
        )
