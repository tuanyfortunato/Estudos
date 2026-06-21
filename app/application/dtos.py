"""DTOs da camada de aplicação.

Estruturas simples de entrada/saída dos use cases, desacopladas dos modelos
de transporte (HTTP/Pydantic) da camada de apresentação.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerateContentInput:
    prompt: str


@dataclass(frozen=True)
class GenerateContentOutput:
    content: str


@dataclass(frozen=True)
class AskInventoryInput:
    question: str
    session_id: str | None = None


@dataclass(frozen=True)
class AskInventoryOutput:
    answer: str
    session_id: str
