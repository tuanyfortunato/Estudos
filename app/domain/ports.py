"""Ports (interfaces) do domínio.

Definem os contratos que a camada de aplicação consome e que a camada de
infraestrutura implementa (princípio da inversão de dependência). Usamos
``typing.Protocol`` para acoplamento estrutural, sem herança obrigatória.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.entities import Conversation, InventoryItem, Message


class InventoryRepository(Protocol):
    """Fonte de dados de inventário (preços de produtos)."""

    def get(self, nome: str) -> InventoryItem | None:
        """Retorna o item pelo nome (case-insensitive) ou ``None``."""
        ...

    def list_all(self) -> list[InventoryItem]:
        """Retorna todos os itens disponíveis."""
        ...


class ConversationRepository(Protocol):
    """Persistência de conversas com estado."""

    def get(self, session_id: str) -> Conversation | None:
        """Retorna a conversa pelo id ou ``None``."""
        ...

    def save(self, conversation: Conversation) -> None:
        """Cria ou atualiza uma conversa."""
        ...


class ContentGenerator(Protocol):
    """Geração de conteúdo de texto (sem estado) a partir de um prompt."""

    def generate(self, prompt: str) -> str:
        """Gera uma resposta de texto para o prompt informado."""
        ...


class InventoryAgent(Protocol):
    """Agente de inventário com Function Calling.

    Recebe o histórico da conversa e a nova pergunta, e devolve a resposta
    final em texto. A execução das ferramentas (consulta de preços) é
    responsabilidade da implementação.
    """

    def answer(self, history: list[Message], question: str) -> str:
        """Responde à pergunta considerando o histórico fornecido."""
        ...
