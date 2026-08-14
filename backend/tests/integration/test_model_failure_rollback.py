from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.clock import FrozenClock
from app.core.config import AppSettings
from app.core.config import ModelProvider as ModelProviderKind
from app.domain.matching import PublicRecommendation
from app.domain.profile import ConstraintStrength, SlotStatus, SlotValue
from app.domain.state import (
    ConversationStage,
    ConversationState,
    MessageRecord,
    MessageRole,
    RecommendationMode,
)
from app.main import create_app
from app.providers.base import (
    ProviderFailure,
    ProviderFailureCode,
    QuestionWordingRequest,
)
from app.providers.deepseek import DeepSeekProvider
from app.repositories.sqlite import SQLiteConversationRepository
from app.services.session_service import SessionService
from app.services.turn_service import TurnService


def _question_request() -> QuestionWordingRequest:
    return QuestionWordingRequest(
        scenarioId="rollback-check",
        stepId="turn-3-question",
        questionId="ask-current-time",
        prompt="平时一天大概能留出多少时间陪它？",
        quickReplies=("半小时左右", "1-2小时", "2小时以上"),
    )


def _completion(
    content: str | None, *, finish_reason: str = "stop"
) -> dict[str, object]:
    return {
        "choices": [
            {
                "finish_reason": finish_reason,
                "message": {"content": content},
            }
        ]
    }


def _provider(handler: httpx.MockTransport) -> DeepSeekProvider:
    return DeepSeekProvider(
        api_key=SecretStr("fake-key"),
        base_url="https://api.deepseek.com/",
        model="deepseek-v4-flash",
        http_client=httpx.Client(transport=handler),
    )


def _seed_conversation(turns: TurnService, clock: FrozenClock) -> ConversationState:
    def add_profile(state: ConversationState) -> ConversationState:
        message = MessageRecord(
            messageId="user-1",
            role=MessageRole.USER,
            content="我更喜欢猫。",
            createdAt=state.lastActiveAt,
        )
        species = SlotValue[tuple[str, ...]](
            value=("CAT",),
            status=SlotStatus.CONFIRMED,
            constraintStrength=ConstraintStrength.PREFERENCE,
            sourceMessageIds=(message.messageId,),
            updatedAt=state.lastActiveAt,
        )
        profile = state.profile.model_copy(update={"speciesScope": species})
        return state.model_copy(update={"messages": (message,), "profile": profile})

    first = turns.process_message(
        "conversation-1",
        client_message_id="client-1",
        base_revision=0,
        mutate=add_profile,
    ).state
    clock.advance(timedelta(minutes=10))

    def add_recommendation(state: ConversationState) -> ConversationState:
        message = MessageRecord(
            messageId="assistant-1",
            role=MessageRole.ASSISTANT,
            content="我先记下你的偏好。",
            createdAt=state.lastActiveAt,
        )
        return state.model_copy(
            update={
                "stage": ConversationStage.RECOMMENDED,
                "recommendationMode": RecommendationMode.PROVISIONAL,
                "messages": (*state.messages, message),
                "recommendations": PublicRecommendation(
                    directions=(),
                    pets=(),
                    priorityMessage="目前是暂定建议。",
                ),
            }
        )

    return turns.process_message(
        "conversation-1",
        client_message_id="client-2",
        base_revision=first.revision,
        mutate=add_recommendation,
    ).state


def _services(
    tmp_path: Path,
) -> tuple[
    TurnService,
    SQLiteConversationRepository,
    FrozenClock,
]:
    clock = FrozenClock(datetime(2026, 8, 14, 9, tzinfo=UTC))
    repository = SQLiteConversationRepository(tmp_path / "sessions.sqlite3")
    repository.initialize()
    sessions = SessionService(repository, clock)
    turns = TurnService(repository, sessions)
    sessions.create("conversation-1")
    return turns, repository, clock


def test_two_invalid_model_responses_do_not_commit_or_refresh_ttl(
    tmp_path: Path,
) -> None:
    turns, repository, clock = _services(tmp_path)
    before = _seed_conversation(turns, clock)
    assert before.revision == 2
    assert before.messages
    assert before.profile.speciesScope.status is SlotStatus.CONFIRMED
    assert before.recommendations is not None
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json=_completion('{"questionId":"ask-current-time"}'),
            request=request,
        )

    provider = _provider(httpx.MockTransport(handler))
    clock.advance(timedelta(hours=3))

    def fail_during_mutation(state: ConversationState) -> ConversationState:
        provider.phrase_question(_question_request())
        return state.model_copy(update={"stage": ConversationStage.DISCOVERING})

    with pytest.raises(ProviderFailure) as error:
        turns.process_message(
            "conversation-1",
            client_message_id="client-failed",
            base_revision=before.revision,
            mutate=fail_during_mutation,
        )

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT
    assert calls == 2
    assert repository.get("conversation-1") == before
    assert repository.get_turn_result("conversation-1", "client-failed") is None


def test_model_timeout_does_not_commit_or_refresh_ttl(tmp_path: Path) -> None:
    turns, repository, clock = _services(tmp_path)
    before = _seed_conversation(turns, clock)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("fake timeout", request=request)

    provider = _provider(httpx.MockTransport(handler))
    clock.advance(timedelta(hours=3))

    def fail_during_mutation(state: ConversationState) -> ConversationState:
        provider.phrase_question(_question_request())
        return state.model_copy(update={"stage": ConversationStage.DISCOVERING})

    with pytest.raises(ProviderFailure) as error:
        turns.process_message(
            "conversation-1",
            client_message_id="client-timeout",
            base_revision=before.revision,
            mutate=fail_during_mutation,
        )

    assert error.value.code is ProviderFailureCode.TIMEOUT
    assert calls == 1
    assert repository.get("conversation-1") == before
    assert repository.get_turn_result("conversation-1", "client-timeout") is None


def test_invalid_model_response_returns_retryable_api_error_with_old_snapshot(
    tmp_path: Path,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_completion(None), request=request)

    repository = SQLiteConversationRepository(tmp_path / "api-sessions.sqlite3")
    provider = _provider(httpx.MockTransport(handler))
    app = create_app(
        settings=AppSettings(modelProvider=ModelProviderKind.MOCK),
        conversation_repository=repository,
        clock=FrozenClock(datetime(2026, 8, 14, 9, tzinfo=UTC)),
        model_provider=provider,
    )
    client = TestClient(app)
    created = client.post("/api/v1/conversations", json={})
    before = created.json()["data"]["conversation"]
    conversation_id = before["conversationId"]

    failed = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-failed",
            "baseRevision": 0,
            "content": "我比较喜欢猫。",
            "quickReplyId": None,
        },
    )

    assert failed.status_code == 502
    assert failed.json()["error"]["code"] == "MODEL_INVALID_RESPONSE"
    assert failed.json()["error"]["retryable"] is True
    assert failed.json()["error"]["details"] == {}
    assert calls == 2
    restored = client.get(f"/api/v1/conversations/{conversation_id}")
    assert restored.json()["data"]["conversation"] == before
    assert repository.get_turn_result(conversation_id, "client-failed") is None
