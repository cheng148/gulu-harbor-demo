from __future__ import annotations

import sqlite3
from pathlib import Path

from app.domain.errors import (
    ConversationAlreadyExistsError,
    ConversationNotFoundError,
    RevisionConflictError,
    SessionExpiredError,
)
from app.domain.state import ConversationStage, ConversationState
from app.repositories.base import TurnCommitResult


class SQLiteConversationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        migration_path = (
            Path(__file__).parent.parent / "db" / "migrations" / "001_init.sql"
        )
        with self._connect() as connection:
            connection.executescript(migration_path.read_text(encoding="utf-8"))

    def create(self, state: ConversationState) -> None:
        payload = state.model_dump_json()
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversations (
                        conversation_id, revision, stage, state_json,
                        created_at, last_active_at, expires_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state.conversationId,
                        state.revision,
                        state.stage.value,
                        payload,
                        state.createdAt.isoformat(),
                        state.lastActiveAt.isoformat(),
                        state.expiresAt.isoformat(),
                        state.lastActiveAt.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise ConversationAlreadyExistsError(state.conversationId) from error

    def get(self, conversation_id: str) -> ConversationState | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        if row is None or row["state_json"] is None:
            return None
        return ConversationState.model_validate_json(row["state_json"])

    def get_terminal_stage(self, conversation_id: str) -> ConversationStage | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT stage, state_json
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
        if row is None or row["state_json"] is not None:
            return None
        return ConversationStage(row["stage"])

    def commit_state(
        self,
        conversation_id: str,
        *,
        expected_revision: int,
        state: ConversationState,
    ) -> None:
        if state.conversationId != conversation_id:
            raise ValueError("state belongs to another conversation")
        if state.revision != expected_revision + 1:
            raise ValueError("committed state revision must increment by one")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT revision, state_json FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None or row["state_json"] is None:
                raise ConversationNotFoundError(conversation_id)
            if row["revision"] != expected_revision:
                raise RevisionConflictError(conversation_id)
            cursor = connection.execute(
                """
                UPDATE conversations
                SET revision = ?, stage = ?, state_json = ?,
                    last_active_at = ?, expires_at = ?, updated_at = ?
                WHERE conversation_id = ? AND revision = ? AND state_json IS NOT NULL
                """,
                (
                    state.revision,
                    state.stage.value,
                    state.model_dump_json(),
                    state.lastActiveAt.isoformat(),
                    state.expiresAt.isoformat(),
                    state.lastActiveAt.isoformat(),
                    conversation_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise RevisionConflictError(conversation_id)

    def tombstone(
        self,
        conversation_id: str,
        *,
        stage: ConversationStage,
        updated_at: str,
    ) -> None:
        if stage not in {ConversationStage.RESET, ConversationStage.EXPIRED}:
            raise ValueError("only terminal stages can be tombstoned")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT stage, state_json FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            if row is None:
                raise ConversationNotFoundError(conversation_id)
            if row["state_json"] is None:
                if row["stage"] == stage.value:
                    return
                raise ConversationNotFoundError(conversation_id)
            connection.execute(
                """
                UPDATE conversations
                SET stage = ?, state_json = NULL, updated_at = ?
                WHERE conversation_id = ?
                """,
                (stage.value, updated_at, conversation_id),
            )
            connection.execute(
                "DELETE FROM processed_messages WHERE conversation_id = ?",
                (conversation_id,),
            )

    def get_turn_result(
        self, conversation_id: str, client_message_id: str
    ) -> ConversationState | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT result_state_json
                FROM processed_messages
                WHERE conversation_id = ? AND client_message_id = ?
                """,
                (conversation_id, client_message_id),
            ).fetchone()
        if row is None:
            return None
        return ConversationState.model_validate_json(row["result_state_json"])

    def commit_turn(
        self,
        conversation_id: str,
        *,
        client_message_id: str,
        expected_revision: int,
        state: ConversationState,
    ) -> TurnCommitResult:
        if state.conversationId != conversation_id:
            raise ValueError("state belongs to another conversation")
        if state.revision != expected_revision + 1:
            raise ValueError("committed state revision must increment by one")

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            receipt = connection.execute(
                """
                SELECT result_state_json
                FROM processed_messages
                WHERE conversation_id = ? AND client_message_id = ?
                """,
                (conversation_id, client_message_id),
            ).fetchone()
            if receipt is not None:
                stored = ConversationState.model_validate_json(
                    receipt["result_state_json"]
                )
                return TurnCommitResult(state=stored, replayed=True)

            row = connection.execute(
                """
                SELECT revision, stage, state_json
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,),
            ).fetchone()
            if row is None or row["stage"] == ConversationStage.RESET.value:
                raise ConversationNotFoundError(conversation_id)
            if row["stage"] == ConversationStage.EXPIRED.value:
                raise SessionExpiredError(conversation_id)
            if row["state_json"] is None:
                raise ConversationNotFoundError(conversation_id)
            if row["revision"] != expected_revision:
                raise RevisionConflictError(conversation_id)

            payload = state.model_dump_json()
            cursor = connection.execute(
                """
                UPDATE conversations
                SET revision = ?, stage = ?, state_json = ?,
                    last_active_at = ?, expires_at = ?, updated_at = ?
                WHERE conversation_id = ? AND revision = ? AND state_json IS NOT NULL
                """,
                (
                    state.revision,
                    state.stage.value,
                    payload,
                    state.lastActiveAt.isoformat(),
                    state.expiresAt.isoformat(),
                    state.lastActiveAt.isoformat(),
                    conversation_id,
                    expected_revision,
                ),
            )
            if cursor.rowcount != 1:
                raise RevisionConflictError(conversation_id)
            connection.execute(
                """
                INSERT INTO processed_messages (
                    conversation_id, client_message_id, base_revision,
                    result_state_json, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    client_message_id,
                    expected_revision,
                    payload,
                    state.lastActiveAt.isoformat(),
                ),
            )
            return TurnCommitResult(state=state, replayed=False)
