"""Adapter de geração de conteúdo usando o Google Gemini."""

from __future__ import annotations

from google import genai

from app.domain.ports import ContentGenerator


class GeminiContentGenerator(ContentGenerator):
    """Implementa ``ContentGenerator`` chamando a API do Gemini."""

    def __init__(self, client: genai.Client, model: str) -> None:
        self._client = client
        self._model = model

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text or ""
