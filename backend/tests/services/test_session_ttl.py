from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import NoReturn

import pytest

from app.core.clock import FrozenClock
from app.domain.errors import SessionExpiredError
from app.domain.state import ConversationStage, ConversationState
from app.repositories.sqlite import SQLiteConversationRepository
from app.services.session_service import SessionService

SessionFixture = tuple[
    SessionService,
    SQLiteConversationRepository,
    FrozenClock,
    datetime,
]


@pytest.fixture
def session(tmp_path: Path) -> SessionFixture:
    start = datetime(2026, 8, 9, 10, tzinfo=UTC)
    clock = FrozenClock(start)
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    service = SessionService(repository, clock)
    return service, repository, clock, start


def test_creation_starts_at_revision_zero_and_expires_after_twenty_four_hours(
    session: SessionFixture,
) -> None:
    service, _, _, start = session

    state = service.create("conversation-1")

    assert state.revision == 0
    assert state.stage is ConversationStage.DISCOVERING
    assert state.lastActiveAt == start
    assert state.expiresAt == start + timedelta(hours=24)


def test_read_only_access_does_not_extend_expiry(session: SessionFixture) -> None:
    service, _, clock, start = session
    service.create("conversation-1")
    clock.advance(timedelta(hours=20))

    restored = service.get("conversation-1")

    assert restored.expiresAt == start + timedelta(hours=24)
    assert restored.lastActiveAt == start


def test_successful_activity_slides_expiry_by_twenty_four_hours(
    session: SessionFixture,
) -> None:
    service, repository, clock, start = session
    service.create("conversation-1")
    clock.advance(timedelta(hours=20))

    updated = service.commit_success(
        "conversation-1",
        base_revision=0,
        mutate=lambda state: state.model_copy(
            update={"stage": ConversationStage.READY_TO_MATCH}
        ),
    )

    assert updated.revision == 1
    assert updated.lastActiveAt == start + timedelta(hours=20)
    assert updated.expiresAt == start + timedelta(hours=44)
    assert repository.get("conversation-1") == updated


def test_failed_activity_does_not_change_revision_or_expiry(
    session: SessionFixture,
) -> None:
    service, repository, clock, start = session
    original = service.create("conversation-1")
    clock.advance(timedelta(hours=20))

    def fail(_state: ConversationState) -> NoReturn:
        raise RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        service.commit_success("conversation-1", base_revision=0, mutate=fail)

    assert repository.get("conversation-1") == original
    assert original.expiresAt == start + timedelta(hours=24)


def test_session_is_expired_at_the_exact_boundary(session: SessionFixture) -> None:
    service, repository, clock, _ = session
    service.create("conversation-1")
    clock.advance(timedelta(hours=24))

    with pytest.raises(SessionExpiredError):
        service.commit_success(
            "conversation-1",
            base_revision=0,
            mutate=lambda state: state,
        )

    assert repository.get("conversation-1") is None
    assert repository.get_terminal_stage("conversation-1") is ConversationStage.EXPIRED
