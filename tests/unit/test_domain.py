"""Testes das entidades de domínio."""

from __future__ import annotations

import pytest

from app.domain.entities import Conversation, InventoryItem, Role


def test_inventory_item_valor_total() -> None:
    item = InventoryItem(nome="notebook", preco_unitario=4500.0)
    assert item.valor_total(3) == 13500.0


def test_inventory_item_quantidade_negativa() -> None:
    item = InventoryItem(nome="notebook", preco_unitario=4500.0)
    with pytest.raises(ValueError):
        item.valor_total(-1)


def test_conversation_add_message_e_history() -> None:
    conv = Conversation(session_id="abc")
    conv.add_message(Role.USER, "olá")
    conv.add_message(Role.ASSISTANT, "oi")

    history = conv.history()
    assert len(history) == 2
    assert history[0].role is Role.USER
    assert history[1].content == "oi"


def test_conversation_gera_session_id_automatico() -> None:
    conv = Conversation()
    assert conv.session_id
