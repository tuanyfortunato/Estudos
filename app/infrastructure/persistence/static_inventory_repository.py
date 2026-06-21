"""Implementação de ``InventoryRepository`` com dados estáticos em memória.

Simula um banco de dados / API de inventário. Em um cenário real, esta classe
seria substituída por um adapter de banco de dados sem alterar o domínio.
"""

from __future__ import annotations

from app.domain.entities import InventoryItem

_PRECOS_PADRAO: dict[str, float] = {
    "notebook": 4500.00,
    "monitor": 1200.00,
    "teclado": 350.00,
}


class StaticInventoryRepository:
    """Repositório de inventário baseado em um dicionário fixo."""

    def __init__(self, precos: dict[str, float] | None = None) -> None:
        precos = precos if precos is not None else _PRECOS_PADRAO
        self._itens: dict[str, InventoryItem] = {
            nome.lower(): InventoryItem(nome=nome.lower(), preco_unitario=preco)
            for nome, preco in precos.items()
        }

    def get(self, nome: str) -> InventoryItem | None:
        return self._itens.get(nome.lower().strip())

    def list_all(self) -> list[InventoryItem]:
        return list(self._itens.values())
