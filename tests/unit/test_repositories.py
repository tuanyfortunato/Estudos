"""Testes dos repositórios em memória."""

from __future__ import annotations

from app.domain.entities import Conversation, Role
from app.infrastructure.persistence.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from app.infrastructure.persistence.static_inventory_repository import (
    StaticInventoryRepository,
)


def test_static_inventory_get_case_insensitive() -> None:
    repo = StaticInventoryRepository({"Notebook": 4500.0})
    item = repo.get("  NOTEBOOK ")
    assert item is not None
    assert item.preco_unitario == 4500.0


def test_static_inventory_get_inexistente() -> None:
    repo = StaticInventoryRepository({"notebook": 4500.0})
    assert repo.get("cadeira") is None


def test_static_inventory_list_all() -> None:
    repo = StaticInventoryRepository({"a": 1.0, "b": 2.0})
    assert len(repo.list_all()) == 2


def test_conversation_repository_save_e_get() -> None:
    repo = InMemoryConversationRepository()
    conv = Conversation(session_id="s1")
    conv.add_message(Role.USER, "oi")
    repo.save(conv)

    loaded = repo.get("s1")
    assert loaded is not None
    assert loaded.session_id == "s1"
    assert len(loaded.messages) == 1


def test_conversation_repository_get_inexistente() -> None:
    repo = InMemoryConversationRepository()
    assert repo.get("nope") is None
