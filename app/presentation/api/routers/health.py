"""Endpoint de health check."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.infrastructure.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Verifica o status da aplicação")
def health(settings: Settings = Depends(get_settings)) -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "gemini_configured": settings.has_api_key,
    }
