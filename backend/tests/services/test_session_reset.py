from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.core.clock import FrozenClock
from app.domain.errors import ConversationNotFoundError, SessionExpiredError
from app.domain.profile import ConstraintStrength, SlotStatus, SlotValue
from app.domain.state import ConversationStage
from app.repositories.sqlite import SQLiteConversationRepository
from app.services.session_service import SessionService

SessionFixture = tuple[
    SessionService,
    SQLiteConversationRepository,
    FrozenClock,
]


@pytest.fixture
def session(tmp_path: Path) -> SessionFixture:
    start = datetime(2026, 8, 9, 10, tzinfo=UTC)
    clock = FrozenClock(start)
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    service = SessionService(repository, clock)
    return service, repository, clock


def test_reset_clears_payload_and_old_id_cannot_be_read(
    session: SessionFixture,
) -> None:
    service, repository, _ = session
    service.create("old-conversation")
    service.commit_success(
        "old-conversation",
        base_revision=0,
        mutate=lambda state: state.model_copy(
            update={
                "profile": state.profile.model_copy(
                    update={
                        "interactionRhythm": SlotValue[str](
                            value="MEDIUM",
                            status=SlotStatus.CONFIRMED,
                            constraintStrength=ConstraintStrength.PREFERENCE,
                            sourceMessageIds=("m-1",),
                            updatedAt=state.lastActiveAt,
                        )
                    }
                )
            }
        ),
    )

    service.reset("old-conversation")

    assert repository.get("old-conversation") is None
    assert repository.get_terminal_stage("old-conversation") is ConversationStage.RESET
    with pytest.raises(ConversationNotFoundError):
        service.get("old-conversation")


def test_reset_is_idempotent_for_an_already_reset_session(
    session: SessionFixture,
) -> None:
    service, _, _ = session
    service.create("conversation-1")

    service.reset("conversation-1")
    service.reset("conversation-1")


def test_new_session_after_reset_starts_with_an_empty_profile(
    session: SessionFixture,
) -> None:
    service, _, _ = session
    service.create("old-conversation")
    service.reset("old-conversation")

    fresh = service.create("new-conversation")

    assert fresh.conversationId == "new-conversation"
    assert fresh.revision == 0
    assert fresh.profile.interactionRhythm.status is SlotStatus.UNKNOWN


def test_expired_session_is_tombstoned_and_payload_is_cleared(
    session: SessionFixture,
) -> None:
    service, repository, clock = session
    service.create("conversation-1")
    clock.advance(timedelta(hours=24, seconds=1))

    with pytest.raises(SessionExpiredError):
        service.get("conversation-1")

    assert repository.get("conversation-1") is None
    assert repository.get_terminal_stage("conversation-1") is ConversationStage.EXPIRED
    with pytest.raises(SessionExpiredError):
        service.get("conversation-1")
