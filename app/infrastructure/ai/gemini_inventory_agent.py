"""Adapter do agente de inventário usando Function Calling do Google Gemini.

Boas práticas aplicadas para agentes de IA:
    * A ferramenta exposta ao modelo é uma *função* (closure), nunca um método
      bound. O SDK faz ``deepcopy`` da config a cada mensagem; um método bound
      arrastaria o ``self`` (e o client, que contém locks de thread não
      copiáveis), causando ``cannot pickle '_thread.lock'``.
    * A ferramenta delega a regra de negócio ao ``InventoryRepository`` do
      domínio, mantendo a lógica de preços fora da camada de IA.
    * O histórico é reconstruído a cada chamada a partir do domínio, deixando a
      persistência da sessão sob controle da aplicação (e não do objeto de chat
      do SDK).

Atenção: este módulo NÃO usa ``from __future__ import annotations``. As anotações
de tipo da ferramenta exposta ao modelo precisam ser *tipos reais* em tempo de
execução, pois o SDK faz ``isinstance(valor, anotação)`` ao executar a função
automaticamente. Com o PEP 563 (anotações como strings), isso quebraria com
``isinstance() arg 2 must be a type``.
"""

from collections.abc import Callable

from google import genai
from google.genai import types

from app.domain.entities import Message, Role
from app.domain.ports import InventoryAgent, InventoryRepository


class GeminiInventoryAgent(InventoryAgent):
    """Implementa ``InventoryAgent`` com Function Calling automático."""

    def __init__(
        self,
        client: genai.Client,
        inventory: InventoryRepository,
        model: str,
        temperature: float,
        system_instruction: str,
    ) -> None:
        self._client = client
        self._model = model
        self._temperature = temperature
        self._system_instruction = system_instruction
        self._tool = self._build_tool(inventory)

    def answer(self, history: list[Message], question: str) -> str:
        config = types.GenerateContentConfig(
            tools=[self._tool],
            temperature=self._temperature,
            system_instruction=self._system_instruction,
        )
        chat = self._client.chats.create(
            model=self._model,
            config=config,
            history=self._to_genai_history(history),
        )
        response = chat.send_message(question)
        return response.text or ""

    @staticmethod
    def _to_genai_history(history: list[Message]) -> list[types.Content]:
        role_map = {Role.USER: "user", Role.ASSISTANT: "model"}
        return [
            types.Content(
                role=role_map[message.role],
                parts=[types.Part(text=message.content)],
            )
            for message in history
        ]

    @staticmethod
    def _build_tool(inventory: InventoryRepository) -> Callable[[str, int], str]:
        """Cria a ferramenta de consulta de preços como uma closure.

        A closure captura apenas o repositório (objeto simples, seguro para
        ``deepcopy``), expondo ao modelo somente os parâmetros relevantes.
        """

        def obter_valor_estoque(produto: str, quantidade: int) -> str:
            """Calcula o valor total de um produto em estoque.

            Args:
                produto: O nome do produto ou equipamento tecnológico.
                quantidade: A quantidade que se deseja cotar.
            """
            item = inventory.get(produto)
            if item is None:
                return f"Produto '{produto}' não encontrado no sistema de inventário."
            total = item.valor_total(quantidade)
            return (
                f"O valor total para {quantidade} unidades de {produto} "
                f"é R$ {total:.2f}."
            )

        return obter_valor_estoque
