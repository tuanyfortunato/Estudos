"""Testes dos use cases usando fakes."""

from __future__ import annotations

import pytest

from app.application.dtos import AskInventoryInput, GenerateContentInput
from app.application.use_cases.ask_inventory_agent import AskInventoryAgentUseCase
from app.application.use_cases.generate_content import GenerateContentUseCase
from app.domain.exceptions import EmptyPromptError
from app.infrastructure.persistence.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from tests.fakes import FakeContentGenerator, FakeInventoryAgent


def test_generate_content_sucesso() -> None:
    generator = FakeContentGenerator(response="ok")
    use_case = GenerateContentUseCase(generator)

    result = use_case.execute(GenerateContentInput(prompt="  olá  "))

    assert result.content == "ok"
    assert generator.received_prompts == ["olá"]  # prompt normalizado


def test_generate_content_prompt_vazio() -> None:
    use_case = GenerateContentUseCase(FakeContentGenerator())
    with pytest.raises(EmptyPromptError):
        use_case.execute(GenerateContentInput(prompt="   "))


def test_ask_inventory_cria_sessao_e_persiste_historico() -> None:
    agent = FakeInventoryAgent(response="R$ 13500,00")
    repo = InMemoryConversationRepository()
    use_case = AskInventoryAgentUseCase(agent, repo)

    result = use_case.execute(AskInventoryInput(question="cota 3 notebooks"))

    assert result.answer == "R$ 13500,00"
    assert result.session_id
    saved = repo.get(result.session_id)
    assert saved is not None
    assert len(saved.messages) == 2  # user + assistant


def test_ask_inventory_mantem_estado_entre_chamadas() -> None:
    agent = FakeInventoryAgent()
    repo = InMemoryConversationRepository()
    use_case = AskInventoryAgentUseCase(agent, repo)

    first = use_case.execute(AskInventoryInput(question="pergunta 1"))
    use_case.execute(
        AskInventoryInput(question="pergunta 2", session_id=first.session_id)
    )

    saved = repo.get(first.session_id)
    assert saved is not None
    assert len(saved.messages) == 4  # 2 rodadas (user+assistant cada)
    # Na 2ª chamada, o agente recebeu o histórico das mensagens anteriores.
    history_passed_on_second_call = agent.calls[1][0]
    assert len(history_passed_on_second_call) == 2


def test_ask_inventory_pergunta_vazia() -> None:
    use_case = AskInventoryAgentUseCase(FakeInventoryAgent(), InMemoryConversationRepository())
    with pytest.raises(EmptyPromptError):
        use_case.execute(AskInventoryInput(question="  "))
