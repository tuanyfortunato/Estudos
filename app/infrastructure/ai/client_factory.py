"""Fábrica do client do Google Gemini."""

from __future__ import annotations

from google import genai

from app.domain.exceptions import DomainError


class MissingApiKeyError(DomainError):
    """Lançada quando a chave de API do Gemini não está configurada."""

    def __init__(self) -> None:
        super().__init__(
            "Chave de API não encontrada. Defina GENAI_API_KEY no arquivo .env."
        )


def create_gemini_client(api_key: str) -> genai.Client:
    if not api_key:
        raise MissingApiKeyError()
    return genai.Client(api_key=api_key)
