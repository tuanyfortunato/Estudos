"""Fábrica da aplicação FastAPI.

Registra routers e mapeia exceções de domínio para respostas HTTP, mantendo
as camadas internas livres de detalhes do framework web.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    ConversationNotFoundError,
    DomainError,
    EmptyPromptError,
    ProductNotFoundError,
)
from app.infrastructure.ai.client_factory import MissingApiKeyError
from app.infrastructure.config import get_settings
from app.presentation.api.routers import content, health, inventory


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "API de estudos de agentes de IA (Google Gemini) estruturada em "
            "Clean Architecture."
        ),
    )

    app.include_router(health.router)
    app.include_router(content.router)
    app.include_router(inventory.router)

    _register_exception_handlers(app)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EmptyPromptError)
    async def _empty_prompt(_: Request, exc: EmptyPromptError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ProductNotFoundError)
    @app.exception_handler(ConversationNotFoundError)
    async def _not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MissingApiKeyError)
    async def _missing_api_key(_: Request, exc: MissingApiKeyError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})


# Instância para os servidores ASGI (uvicorn app.presentation.api.app:app)
app = create_app()
