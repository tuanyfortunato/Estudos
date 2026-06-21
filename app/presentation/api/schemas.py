"""Schemas Pydantic de entrada e saída da API (camada de transporte).

Separados dos DTOs da aplicação para que mudanças no contrato HTTP não afetem
os use cases, e vice-versa.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateContentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt para geração de conteúdo.")

    model_config = {
        "json_schema_extra": {
            "examples": [{"prompt": "Escreva um haicai sobre tecnologia."}]
        }
    }


class GenerateContentResponse(BaseModel):
    content: str


class AskInventoryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Pergunta ao agente de inventário.")
    session_id: str | None = Field(
        default=None,
        description="Identificador da sessão para manter o histórico. "
        "Se omitido, uma nova sessão é criada.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"question": "Preciso cotar o preço de 3 notebooks.", "session_id": None}
            ]
        }
    }


class AskInventoryResponse(BaseModel):
    answer: str
    session_id: str


class InventoryItemResponse(BaseModel):
    nome: str
    preco_unitario: float


class ErrorResponse(BaseModel):
    detail: str
