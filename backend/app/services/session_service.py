from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from app.core.clock import Clock
from app.domain.errors import (
    ConversationNotFoundError,
    RevisionConflictError,
    SessionExpiredError,
)
from app.domain.state import ConversationStage, ConversationState
from app.repositories.base import ConversationRepository

SESSION_TTL = timedelta(hours=24)
StateMutator = Callable[[ConversationState], ConversationState]


class SessionService:
    def __init__(self, repository: ConversationRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def create(self, conversation_id: str) -> ConversationState:
        now = self._clock.now()
        state = ConversationState(
            conversationId=conversation_id,
            revision=0,
            stage=ConversationStage.DISCOVERING,
            createdAt=now,
            lastActiveAt=now,
            expiresAt=now + SESSION_TTL,
        )
        self._repository.create(state)
        return state

    def get(self, conversation_id: str) -> ConversationState:
        return self._require_active(conversation_id)

    def reset(self, conversation_id: str) -> None:
        terminal_stage = self._repository.get_terminal_stage(conversation_id)
        if terminal_stage is ConversationStage.RESET:
            return
        if terminal_stage is ConversationStage.EXPIRED:
            raise SessionExpiredError(conversation_id)

        state = self._repository.get(conversation_id)
        if state is None:
            raise ConversationNotFoundError(conversation_id)
        if self._clock.now() >= state.expiresAt:
            self._expire(conversation_id)
            raise SessionExpiredError(conversation_id)
        self._repository.tombstone(
            conversation_id,
            stage=ConversationStage.RESET,
            updated_at=self._clock.now().isoformat(),
        )

    def commit_success(
        self,
        conversation_id: str,
        *,
        base_revision: int,
        mutate: StateMutator,
    ) -> ConversationState:
        current = self._require_active(conversation_id)
        updated = self.prepare_successful_state(
            current,
            base_revision=base_revision,
            mutate=mutate,
        )
        self._repository.commit_state(
            conversation_id,
            expected_revision=base_revision,
            state=updated,
        )
        return updated

    def prepare_successful_state(
        self,
        current: ConversationState,
        *,
        base_revision: int,
        mutate: StateMutator,
    ) -> ConversationState:
        if current.revision != base_revision:
            raise RevisionConflictError(current.conversationId)
        draft = mutate(current)
        if draft.conversationId != current.conversationId:
            raise ValueError("mutator returned another conversation")

        now = self._clock.now()
        payload = draft.model_dump(mode="python")
        payload.update(
            revision=base_revision + 1,
            createdAt=current.createdAt,
            lastActiveAt=now,
            expiresAt=now + SESSION_TTL,
        )
        return ConversationState.model_validate(payload)

    def _require_active(self, conversation_id: str) -> ConversationState:
        state = self._repository.get(conversation_id)
        if state is None:
            terminal_stage = self._repository.get_terminal_stage(conversation_id)
            if terminal_stage is ConversationStage.EXPIRED:
                raise SessionExpiredError(conversation_id)
            raise ConversationNotFoundError(conversation_id)
        if self._clock.now() >= state.expiresAt:
            self._expire(conversation_id)
            raise SessionExpiredError(conversation_id)
        return state

    def _expire(self, conversation_id: str) -> None:
        self._repository.tombstone(
            conversation_id,
            stage=ConversationStage.EXPIRED,
            updated_at=self._clock.now().isoformat(),
        )
