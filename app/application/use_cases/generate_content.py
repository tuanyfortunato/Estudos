"""Use case: gerar conteúdo de texto a partir de um prompt (sem estado)."""

from __future__ import annotations

from app.application.dtos import GenerateContentInput, GenerateContentOutput
from app.domain.exceptions import EmptyPromptError
from app.domain.ports import ContentGenerator


class GenerateContentUseCase:
    """Orquestra a geração de conteúdo, aplicando as regras de negócio."""

    def __init__(self, content_generator: ContentGenerator) -> None:
        self._content_generator = content_generator

    def execute(self, data: GenerateContentInput) -> GenerateContentOutput:
        prompt = data.prompt.strip()
        if not prompt:
            raise EmptyPromptError("O prompt não pode estar vazio.")

        content = self._content_generator.generate(prompt)
        return GenerateContentOutput(content=content)
