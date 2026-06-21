"""Endpoints de geração de conteúdo."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.dtos import GenerateContentInput
from app.application.use_cases.generate_content import GenerateContentUseCase
from app.presentation.api.dependencies import get_generate_content_use_case
from app.presentation.api.schemas import (
    GenerateContentRequest,
    GenerateContentResponse,
)

router = APIRouter(prefix="/content", tags=["content"])


@router.post(
    "",
    response_model=GenerateContentResponse,
    summary="Gera conteúdo de texto a partir de um prompt",
)
def generate_content(
    payload: GenerateContentRequest,
    use_case: GenerateContentUseCase = Depends(get_generate_content_use_case),
) -> GenerateContentResponse:
    result = use_case.execute(GenerateContentInput(prompt=payload.prompt))
    return GenerateContentResponse(content=result.content)
