from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.domain.state import ConversationStage, ConversationState


@dataclass(frozen=True)
class TurnCommitResult:
    state: ConversationState
    replayed: bool


class ConversationRepository(Protocol):
    database_path: Path

    def initialize(self) -> None: ...

    def create(self, state: ConversationState) -> None: ...

    def get(self, conversation_id: str) -> ConversationState | None: ...

    def get_terminal_stage(self, conversation_id: str) -> ConversationStage | None: ...

    def commit_state(
        self,
        conversation_id: str,
        *,
        expected_revision: int,
        state: ConversationState,
    ) -> None: ...

    def tombstone(
        self,
        conversation_id: str,
        *,
        stage: ConversationStage,
        updated_at: str,
    ) -> None: ...

    def get_turn_result(
        self, conversation_id: str, client_message_id: str
    ) -> ConversationState | None: ...

    def commit_turn(
        self,
        conversation_id: str,
        *,
        client_message_id: str,
        expected_revision: int,
        state: ConversationState,
    ) -> TurnCommitResult: ...
