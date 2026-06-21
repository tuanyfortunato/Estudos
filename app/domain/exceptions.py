"""Exceções de domínio.

Erros de regra de negócio são representados por exceções próprias do domínio,
independentes de framework. As camadas externas (ex.: API) traduzem essas
exceções para os formatos adequados (ex.: status HTTP).
"""

from __future__ import annotations


class DomainError(Exception):
    """Erro base do domínio."""


class EmptyPromptError(DomainError):
    """Lançada quando um prompt/pergunta obrigatório está vazio."""


class ProductNotFoundError(DomainError):
    """Lançada quando um produto não existe no inventário."""

    def __init__(self, produto: str) -> None:
        self.produto = produto
        super().__init__(f"Produto '{produto}' não encontrado no inventário.")


class ConversationNotFoundError(DomainError):
    """Lançada quando uma conversa (sessão) não existe."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        super().__init__(f"Conversa '{session_id}' não encontrada.")
