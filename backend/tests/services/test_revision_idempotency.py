from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NoReturn

import pytest

from app.core.clock import FrozenClock
from app.domain.errors import RevisionConflictError
from app.domain.state import ConversationState, MessageRecord, MessageRole
from app.repositories.sqlite import SQLiteConversationRepository
from app.services.session_service import SessionService, StateMutator
from app.services.turn_service import TurnService

TurnFixture = tuple[
    TurnService,
    SessionService,
    SQLiteConversationRepository,
    FrozenClock,
    datetime,
]


@pytest.fixture
def turn(tmp_path: Path) -> TurnFixture:
    start = datetime(2026, 8, 9, 10, tzinfo=UTC)
    clock = FrozenClock(start)
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    sessions = SessionService(repository, clock)
    turns = TurnService(repository, sessions)
    sessions.create("conversation-1")
    return turns, sessions, repository, clock, start


def append_message(message_id: str, content: str) -> StateMutator:
    def mutate(state: ConversationState) -> ConversationState:
        message = MessageRecord(
            messageId=message_id,
            role=MessageRole.USER,
            content=content,
            createdAt=state.lastActiveAt,
        )
        return state.model_copy(update={"messages": (*state.messages, message)})

    return mutate


def test_duplicate_client_message_id_returns_first_result_without_second_write(
    turn: TurnFixture,
) -> None:
    turns, _, repository, clock, start = turn
    first = turns.process_message(
        "conversation-1",
        client_message_id="client-message-1",
        base_revision=0,
        mutate=append_message("user-message-1", "我喜欢猫"),
    )
    clock.advance(timedelta(hours=1))

    duplicate = turns.process_message(
        "conversation-1",
        client_message_id="client-message-1",
        base_revision=0,
        mutate=lambda _state: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert first.replayed is False
    assert duplicate.replayed is True
    assert duplicate.state == first.state
    assert duplicate.state.revision == 1
    assert len(duplicate.state.messages) == 1
    assert duplicate.state.expiresAt == start + timedelta(hours=24)
    assert repository.get("conversation-1") == first.state


def test_stale_base_revision_is_rejected_without_changing_state(
    turn: TurnFixture,
) -> None:
    turns, _, repository, _, _ = turn
    first = turns.process_message(
        "conversation-1",
        client_message_id="client-message-1",
        base_revision=0,
        mutate=append_message("user-message-1", "我喜欢猫"),
    )

    with pytest.raises(RevisionConflictError):
        turns.process_message(
            "conversation-1",
            client_message_id="client-message-2",
            base_revision=0,
            mutate=append_message("user-message-2", "我也喜欢狗"),
        )

    assert repository.get("conversation-1") == first.state


def test_failed_processing_leaves_no_partial_state_or_idempotency_record(
    turn: TurnFixture,
) -> None:
    turns, _, repository, clock, start = turn

    def fail(_state: ConversationState) -> NoReturn:
        raise RuntimeError("model unavailable")

    with pytest.raises(RuntimeError, match="model unavailable"):
        turns.process_message(
            "conversation-1",
            client_message_id="client-message-1",
            base_revision=0,
            mutate=fail,
        )

    unchanged = repository.get("conversation-1")
    assert unchanged is not None
    assert unchanged.revision == 0
    assert unchanged.messages == ()
    assert unchanged.expiresAt == start + timedelta(hours=24)
    assert repository.get_turn_result("conversation-1", "client-message-1") is None

    clock.advance(timedelta(minutes=5))
    retry = turns.process_message(
        "conversation-1",
        client_message_id="client-message-1",
        base_revision=0,
        mutate=append_message("user-message-1", "重新发送"),
    )
    assert retry.replayed is False
    assert retry.state.revision == 1


def test_message_ids_are_scoped_to_each_conversation(turn: TurnFixture) -> None:
    turns, sessions, _, _, _ = turn
    sessions.create("conversation-2")

    first = turns.process_message(
        "conversation-1",
        client_message_id="same-client-id",
        base_revision=0,
        mutate=append_message("user-message-1", "第一段会话"),
    )
    second = turns.process_message(
        "conversation-2",
        client_message_id="same-client-id",
        base_revision=0,
        mutate=append_message("user-message-2", "第二段会话"),
    )

    assert first.replayed is False
    assert second.replayed is False
    assert first.state.conversationId != second.state.conversationId
