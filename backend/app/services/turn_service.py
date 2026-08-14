from __future__ import annotations

from app.domain.state import ConversationState
from app.repositories.base import ConversationRepository, TurnCommitResult
from app.services.session_service import SessionService, StateMutator


class TurnService:
    def __init__(
        self,
        repository: ConversationRepository,
        sessions: SessionService,
    ) -> None:
        self._repository = repository
        self._sessions = sessions

    def get_stored_result(
        self, conversation_id: str, client_message_id: str
    ) -> ConversationState | None:
        self._sessions.get(conversation_id)
        return self._repository.get_turn_result(conversation_id, client_message_id)
    def process_message(
        self,
        conversation_id: str,
        *,
        client_message_id: str,
        base_revision: int,
        mutate: StateMutator,
    ) -> TurnCommitResult:
        if not client_message_id:
            raise ValueError("client message ID cannot be empty")
        current = self._sessions.get(conversation_id)
        stored = self._repository.get_turn_result(conversation_id, client_message_id)
        if stored is not None:
            return TurnCommitResult(state=stored, replayed=True)

        updated = self._sessions.prepare_successful_state(
            current,
            base_revision=base_revision,
            mutate=mutate,
        )
        return self._repository.commit_turn(
            conversation_id,
            client_message_id=client_message_id,
            expected_revision=base_revision,
            state=updated,
        )
