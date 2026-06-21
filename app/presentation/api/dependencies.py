"""Composition root: monta o grafo de dependências da aplicação.

Aqui as implementações concretas (infraestrutura) são conectadas aos ports
consumidos pelos use cases. O uso de ``lru_cache`` garante instâncias únicas
(singletons) para recursos que devem ser compartilhados entre requisições,
como o client do Gemini e o repositório de conversas (estado das sessões).
"""

from __future__ import annotations

from functools import lru_cache

from google import genai

from app.application.use_cases.ask_inventory_agent import AskInventoryAgentUseCase
from app.application.use_cases.generate_content import GenerateContentUseCase
from app.domain.ports import ConversationRepository, InventoryRepository
from app.infrastructure.ai.client_factory import create_gemini_client
from app.infrastructure.ai.gemini_content_generator import GeminiContentGenerator
from app.infrastructure.ai.gemini_inventory_agent import GeminiInventoryAgent
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.persistence.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from app.infrastructure.persistence.static_inventory_repository import (
    StaticInventoryRepository,
)


@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return create_gemini_client(settings.genai_api_key)


@lru_cache
def get_inventory_repository() -> InventoryRepository:
    return StaticInventoryRepository()


@lru_cache
def get_conversation_repository() -> ConversationRepository:
    return InMemoryConversationRepository()


def get_generate_content_use_case() -> GenerateContentUseCase:
    settings: Settings = get_settings()
    generator = GeminiContentGenerator(
        client=get_gemini_client(),
        model=settings.gemini_model,
    )
    return GenerateContentUseCase(content_generator=generator)


def get_ask_inventory_use_case() -> AskInventoryAgentUseCase:
    settings: Settings = get_settings()
    agent = GeminiInventoryAgent(
        client=get_gemini_client(),
        inventory=get_inventory_repository(),
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        system_instruction=settings.agent_system_instruction,
    )
    return AskInventoryAgentUseCase(
        agent=agent,
        conversations=get_conversation_repository(),
    )
