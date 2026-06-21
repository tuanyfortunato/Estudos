"""Testes de integração da API com dependências sobrescritas (sem rede)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.application.use_cases.ask_inventory_agent import AskInventoryAgentUseCase
from app.application.use_cases.generate_content import GenerateContentUseCase
from app.presentation.api.app import create_app
from app.presentation.api.dependencies import (
    get_ask_inventory_use_case,
    get_generate_content_use_case,
)
from app.infrastructure.persistence.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from tests.fakes import FakeContentGenerator, FakeInventoryAgent


@pytest.fixture
def client() -> TestClient:
    app = create_app()

    content_uc = GenerateContentUseCase(FakeContentGenerator(response="texto fake"))
    inventory_uc = AskInventoryAgentUseCase(
        FakeInventoryAgent(response="resposta fake"),
        InMemoryConversationRepository(),
    )

    app.dependency_overrides[get_generate_content_use_case] = lambda: content_uc
    app.dependency_overrides[get_ask_inventory_use_case] = lambda: inventory_uc
    return TestClient(app)


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_content(client: TestClient) -> None:
    resp = client.post("/content", json={"prompt": "olá"})
    assert resp.status_code == 200
    assert resp.json() == {"content": "texto fake"}


def test_generate_content_prompt_vazio_validacao(client: TestClient) -> None:
    resp = client.post("/content", json={"prompt": ""})
    assert resp.status_code == 422  # validação do Pydantic (min_length)


def test_inventory_ask_mantem_sessao(client: TestClient) -> None:
    first = client.post("/inventory/ask", json={"question": "cota 3 notebooks"})
    assert first.status_code == 200
    session_id = first.json()["session_id"]
    assert session_id

    second = client.post(
        "/inventory/ask",
        json={"question": "e 2 monitores?", "session_id": session_id},
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id


def test_inventory_items(client: TestClient) -> None:
    resp = client.get("/inventory/items")
    assert resp.status_code == 200
    nomes = {item["nome"] for item in resp.json()}
    assert "notebook" in nomes
