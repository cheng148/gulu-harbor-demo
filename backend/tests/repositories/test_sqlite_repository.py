from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.errors import RevisionConflictError
from app.domain.state import ConversationStage, ConversationState
from app.repositories.sqlite import SQLiteConversationRepository


def state(
    *, revision: int = 0, stage: ConversationStage = ConversationStage.DISCOVERING
) -> ConversationState:
    now = datetime(2026, 8, 9, 10, tzinfo=UTC)
    return ConversationState(
        conversationId="conversation-1",
        revision=revision,
        stage=stage,
        createdAt=now,
        lastActiveAt=now,
        expiresAt=now + timedelta(hours=24),
    )


def test_repository_creates_and_reads_a_conversation(tmp_path: Path) -> None:
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()

    repository.create(state())

    assert repository.get("conversation-1") == state()


def test_repository_atomically_commits_the_expected_revision(tmp_path: Path) -> None:
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    repository.create(state())
    updated = state(revision=1, stage=ConversationStage.READY_TO_MATCH)

    repository.commit_state("conversation-1", expected_revision=0, state=updated)

    assert repository.get("conversation-1") == updated


def test_revision_conflict_leaves_the_stored_state_unchanged(tmp_path: Path) -> None:
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    original = state()
    repository.create(original)

    with pytest.raises(RevisionConflictError):
        repository.commit_state(
            "conversation-1",
            expected_revision=7,
            state=state(revision=8),
        )

    assert repository.get("conversation-1") == original
