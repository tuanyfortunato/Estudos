"""Entidades e objetos de valor do domínio.

Modelos puros, sem dependência de frameworks. Representam os conceitos
centrais do negócio: itens de inventário e conversas com o agente.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True)
class InventoryItem:
    """Item de inventário com preço unitário."""

    nome: str
    preco_unitario: float

    def valor_total(self, quantidade: int) -> float:
        """Calcula o valor total para uma dada quantidade."""
        if quantidade < 0:
            raise ValueError("A quantidade não pode ser negativa.")
        return self.preco_unitario * quantidade


class Role(str, Enum):
    """Autor de uma mensagem dentro de uma conversa."""

    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class Message:
    """Mensagem trocada entre o usuário e o agente."""

    role: Role
    content: str
    created_at: datetime = field(default_factory=_now)


@dataclass
class Conversation:
    """Conversa com estado (histórico) identificada por um session_id."""

    session_id: str = field(default_factory=_new_id)
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def add_message(self, role: Role, content: str) -> Message:
        """Adiciona uma mensagem ao histórico e atualiza o timestamp."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = _now()
        return message

    def history(self) -> list[Message]:
        """Retorna uma cópia imutável do histórico atual."""
        return list(self.messages)
