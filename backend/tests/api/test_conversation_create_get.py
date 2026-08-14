from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.clock import FrozenClock
from app.core.config import AppSettings, ModelProvider
from app.main import create_app
from app.repositories.sqlite import SQLiteConversationRepository


@pytest.fixture
def api(tmp_path: Path) -> tuple[TestClient, FrozenClock]:
    clock = FrozenClock(datetime(2026, 8, 12, 9, tzinfo=UTC))
    repository = SQLiteConversationRepository(tmp_path / "api.sqlite3")
    app = create_app(
        settings=AppSettings(modelProvider=ModelProvider.MOCK),
        conversation_repository=repository,
        clock=clock,
    )
    return TestClient(app), clock


def test_create_conversation_returns_the_public_initial_state(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api

    response = client.post("/api/v1/conversations", json={"clientLocale": "zh-CN"})

    assert response.status_code == 201
    body = response.json()
    conversation = body["data"]["conversation"]
    assert conversation["revision"] == 0
    assert conversation["stage"] == "DISCOVERING"
    assert conversation["recommendationMode"] == "NONE"
    assert {item["status"] for item in conversation["profileSummary"].values()} == {
        "UNKNOWN"
    }
    assert all(
        item["value"] is None for item in conversation["profileSummary"].values()
    )
    assert body["data"]["nextQuestion"]["questionId"] == "ask-current-time"
    assert "普通工作日" in body["data"]["nextQuestion"]["text"]
    assert body["data"]["assistantMessage"]["role"] == "ASSISTANT"
    assert body["meta"]["requestId"]


def test_get_restores_the_same_conversation_without_extending_expiry(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, clock = api
    created = client.post("/api/v1/conversations", json={}).json()
    original = created["data"]["conversation"]
    conversation_id = original["conversationId"]
    clock.advance(timedelta(hours=20))

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 200
    restored = response.json()["data"]
    assert restored["conversation"] == original
    assert restored["currentQuestion"]["questionId"] == "ask-current-time"
    assert restored["recommendation"] is None
    assert restored["messages"][0]["role"] == "ASSISTANT"


def test_get_returns_not_found_for_an_unknown_conversation(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api

    response = client.get("/api/v1/conversations/conv_missing")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "CONVERSATION_NOT_FOUND",
        "message": "没有找到这段选宠对话，请重新开始。",
        "retryable": False,
        "details": {},
    }


def test_get_returns_gone_at_the_twenty_four_hour_boundary(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, clock = api
    created = client.post("/api/v1/conversations", json={}).json()
    conversation_id = created["data"]["conversation"]["conversationId"]
    clock.advance(timedelta(hours=24))

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 410
    assert response.json()["error"] == {
        "code": "SESSION_EXPIRED",
        "message": "这段对话已保存满24小时，请重新开始。",
        "retryable": False,
        "details": {},
    }


def test_public_response_does_not_leak_internal_fields_or_numeric_scores(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api

    response = client.post("/api/v1/conversations", json={})

    for internal_name in (
        "schemaVersion",
        "sourceMessageIds",
        "questionHistory",
        "retrievedSourceIds",
        "directionCandidates",
        "petCandidateIds",
        "internalScore",
        "systemPrompt",
    ):
        assert internal_name not in response.text


def test_create_rejects_an_unsupported_locale(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api

    response = client.post("/api/v1/conversations", json={"clientLocale": "en-US"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
