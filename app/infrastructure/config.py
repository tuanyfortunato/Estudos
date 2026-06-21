"""Configuração da aplicação via variáveis de ambiente.

Centraliza todas as configurações usando ``pydantic-settings``, com validação
e valores padrão. As variáveis são lidas do ambiente e/ou de um arquivo ``.env``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações tipadas da aplicação."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Credenciais / modelo do Gemini
    genai_api_key: str = Field(
        default="",
        validation_alias="GENAI_API_KEY",
        description="Chave de API do Google Gemini.",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias="GEMINI_MODEL",
        description="Modelo do Gemini utilizado nas chamadas.",
    )
    gemini_temperature: float = Field(default=0.2, validation_alias="GEMINI_TEMPERATURE")

    agent_system_instruction: str = Field(
        default="Você é um assistente técnico de inventário útil e direto.",
        validation_alias="AGENT_SYSTEM_INSTRUCTION",
    )

    # Metadados da API
    app_name: str = Field(default="AI Studies API", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")

    @property
    def has_api_key(self) -> bool:
        return bool(self.genai_api_key)


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância única (cacheada) das configurações."""
    return Settings()
