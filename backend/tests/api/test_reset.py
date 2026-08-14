from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.core.clock import FrozenClock
from app.core.config import AppSettings, ModelProvider
from app.main import create_app
from app.repositories.sqlite import SQLiteConversationRepository


@pytest.fixture
def api(tmp_path: Path) -> tuple[TestClient, FrozenClock]:
    clock = FrozenClock(datetime(2026, 8, 12, 14, tzinfo=UTC))
    repository = SQLiteConversationRepository(tmp_path / "reset-api.sqlite3")
    app = create_app(
        settings=AppSettings(modelProvider=ModelProvider.MOCK),
        conversation_repository=repository,
        clock=clock,
    )
    return TestClient(app), clock


def _create(client: TestClient) -> str:
    response = client.post("/api/v1/conversations", json={})
    body = cast(dict[str, Any], response.json())
    return cast(str, body["data"]["conversation"]["conversationId"])


def test_reset_returns_no_content_and_old_session_cannot_be_restored(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id = _create(client)

    response = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204
    assert response.content == b""
    restored = client.get(f"/api/v1/conversations/{conversation_id}")
    assert restored.status_code == 404
    assert restored.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_reset_is_idempotent_for_an_already_reset_session(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id = _create(client)

    first = client.delete(f"/api/v1/conversations/{conversation_id}")
    second = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert first.status_code == second.status_code == 204
    assert first.content == second.content == b""


def test_reset_unknown_session_returns_not_found(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api

    response = client.delete("/api/v1/conversations/conv_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_reset_expired_session_returns_gone(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, clock = api
    conversation_id = _create(client)
    clock.advance(timedelta(hours=24))

    response = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"


def test_new_session_after_reset_has_a_different_id_and_empty_profile(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    old_id = _create(client)
    client.delete(f"/api/v1/conversations/{old_id}")

    created = client.post("/api/v1/conversations", json={})

    conversation = created.json()["data"]["conversation"]
    assert conversation["conversationId"] != old_id
    assert conversation["revision"] == 0
    assert {slot["status"] for slot in conversation["profileSummary"].values()} == {
        "UNKNOWN"
    }
