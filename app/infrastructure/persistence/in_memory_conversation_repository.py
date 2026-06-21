"""Implementação de ``ConversationRepository`` em memória, thread-safe.

Mantém as conversas em um dicionário protegido por lock. Adequado para estudos
e desenvolvimento; em produção seria trocado por Redis/banco de dados.
"""

from __future__ import annotations

import threading

from app.domain.entities import Conversation


class InMemoryConversationRepository:
    """Armazena conversas indexadas por ``session_id``."""

    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Conversation | None:
        with self._lock:
            return self._store.get(session_id)

    def save(self, conversation: Conversation) -> None:
        with self._lock:
            self._store[conversation.session_id] = conversation
