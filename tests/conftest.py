"""Configuração compartilhada de testes."""

from __future__ import annotations

import pytest

from app.infrastructure.persistence.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from app.infrastructure.persistence.static_inventory_repository import (
    StaticInventoryRepository,
)


@pytest.fixture
def inventory_repo() -> StaticInventoryRepository:
    return StaticInventoryRepository({"notebook": 4500.0, "monitor": 1200.0})


@pytest.fixture
def conversation_repo() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()
