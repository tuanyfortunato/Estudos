"""Use case: conversar com o agente de inventário mantendo estado por sessão."""

from __future__ import annotations

from app.application.dtos import AskInventoryInput, AskInventoryOutput
from app.domain.entities import Conversation, Role
from app.domain.exceptions import EmptyPromptError
from app.domain.ports import ConversationRepository, InventoryAgent


class AskInventoryAgentUseCase:
    """Orquestra uma rodada de conversa com o agente de inventário.

    Fluxo:
        1. Recupera (ou cria) a conversa pelo ``session_id``.
        2. Chama o agente passando o histórico e a nova pergunta.
        3. Persiste as mensagens do usuário e do assistente.
        4. Retorna a resposta e o ``session_id`` da conversa.
    """

    def __init__(
        self,
        agent: InventoryAgent,
        conversations: ConversationRepository,
    ) -> None:
        self._agent = agent
        self._conversations = conversations

    def execute(self, data: AskInventoryInput) -> AskInventoryOutput:
        question = data.question.strip()
        if not question:
            raise EmptyPromptError("A pergunta não pode estar vazia.")

        conversation = self._load_or_create(data.session_id)

        answer = self._agent.answer(conversation.history(), question)

        conversation.add_message(Role.USER, question)
        conversation.add_message(Role.ASSISTANT, answer)
        self._conversations.save(conversation)

        return AskInventoryOutput(answer=answer, session_id=conversation.session_id)

    def _load_or_create(self, session_id: str | None) -> Conversation:
        if session_id:
            existing = self._conversations.get(session_id)
            if existing is not None:
                return existing
            return Conversation(session_id=session_id)
        return Conversation()
