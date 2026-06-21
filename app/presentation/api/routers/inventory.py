"""Endpoints do agente de inventário."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.dtos import AskInventoryInput
from app.application.use_cases.ask_inventory_agent import AskInventoryAgentUseCase
from app.domain.ports import InventoryRepository
from app.presentation.api.dependencies import (
    get_ask_inventory_use_case,
    get_inventory_repository,
)
from app.presentation.api.schemas import (
    AskInventoryRequest,
    AskInventoryResponse,
    InventoryItemResponse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post(
    "/ask",
    response_model=AskInventoryResponse,
    summary="Conversa com o agente de inventário (com Function Calling)",
)
def ask_inventory(
    payload: AskInventoryRequest,
    use_case: AskInventoryAgentUseCase = Depends(get_ask_inventory_use_case),
) -> AskInventoryResponse:
    result = use_case.execute(
        AskInventoryInput(question=payload.question, session_id=payload.session_id)
    )
    return AskInventoryResponse(answer=result.answer, session_id=result.session_id)


@router.get(
    "/items",
    response_model=list[InventoryItemResponse],
    summary="Lista os itens disponíveis no inventário",
)
def list_items(
    inventory: InventoryRepository = Depends(get_inventory_repository),
) -> list[InventoryItemResponse]:
    return [
        InventoryItemResponse(nome=item.nome, preco_unitario=item.preco_unitario)
        for item in inventory.list_all()
    ]
