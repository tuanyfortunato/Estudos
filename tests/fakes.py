"""Implementações fake dos ports para testes determinísticos (sem rede)."""

from __future__ import annotations

from app.domain.entities import Message
from app.domain.ports import ContentGenerator, InventoryAgent


class FakeContentGenerator(ContentGenerator):
    def __init__(self, response: str = "conteúdo gerado") -> None:
        self.response = response
        self.received_prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.received_prompts.append(prompt)
        return self.response


class FakeInventoryAgent(InventoryAgent):
    def __init__(self, response: str = "resposta do agente") -> None:
        self.response = response
        self.calls: list[tuple[list[Message], str]] = []

    def answer(self, history: list[Message], question: str) -> str:
        self.calls.append((history, question))
        return self.response
