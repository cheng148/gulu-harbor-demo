from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from app.core.clock import FrozenClock
from app.core.config import AppSettings
from app.core.config import ModelProvider as ModelProviderKind
from app.domain.profile import SlotStatus
from app.domain.profile_merge import ProfileChange, ProfileDelta
from app.main import create_app
from app.providers.base import (
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    QuestionWordingRequest,
    QuestionWordingResponse,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    SafetyReviewRequest,
    SafetyReviewResponse,
)
from app.repositories.sqlite import SQLiteConversationRepository


class DeterministicAPIProvider:
    def extract_profile(
        self, request: ProfileExtractionRequest
    ) -> ProfileExtractionResponse:
        changes: tuple[ProfileChange, ...]
        if request.text == "我的时间比较充足，喜欢安静陪在附近，也能接受日常打理。":
            changes = (
                ProfileChange(
                    slotName="speciesScope",
                    value=("CAT",),
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="currentTimeArrangement",
                    value="TIME_FLEXIBLE",
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="interactionRhythm",
                    value="LOW_MEDIUM",
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="companionshipDistance",
                    value="NEARBY",
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="ongoingInvestmentWillingness",
                    value="MEDIUM",
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="disturbanceTolerance",
                    value=("SHEDDING_MEDIUM_HIGH", "NOISE_LOW"),
                    status=SlotStatus.CONFIRMED,
                ),
                ProfileChange(
                    slotName="absoluteBottomLines",
                    value=(),
                    status=SlotStatus.CONFIRMED,
                ),
            )
        elif request.text == "猫狗都不过敏。":
            changes = (
                ProfileChange(
                    slotName="allergySpecies",
                    value=(),
                    status=SlotStatus.CONFIRMED,
                ),
            )
        else:
            changes = ()
        return ProfileExtractionResponse(
            delta=ProfileDelta(
                sourceMessageId=request.messageId,
                changes=changes,
            )
        )

    def phrase_question(
        self, request: QuestionWordingRequest
    ) -> QuestionWordingResponse:
        return QuestionWordingResponse(
            questionId=request.questionId,
            text=request.prompt,
            quickReplies=request.quickReplies,
        )

    def explain_recommendation(
        self, request: RecommendationExplanationRequest
    ) -> RecommendationExplanationResponse:
        return RecommendationExplanationResponse(
            intro="我把这次更值得认识的方向和伙伴整理好了。",
            items=tuple(
                f"{fact.subjectId}会保留原来的匹配结论和事实。"
                for fact in request.facts
            ),
        )

    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        del request
        return SafetyReviewResponse(isApproved=True)


class InvalidExplanationProvider(DeterministicAPIProvider):
    def explain_recommendation(
        self, request: RecommendationExplanationRequest
    ) -> RecommendationExplanationResponse:
        del request
        return RecommendationExplanationResponse(
            intro="这段说明缺少逐项对应。",
            items=(),
        )


class RejectedSafetyProvider(DeterministicAPIProvider):
    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        del request
        return SafetyReviewResponse(
            isApproved=False,
            flags=("包含未经支持的保证",),
        )


class ReplacedSafetyProvider(DeterministicAPIProvider):
    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        return SafetyReviewResponse(
            isApproved=False,
            flags=("已改为谨慎表达",),
            safeReplacementTexts=tuple(
                f"安全版本{index + 1}" for index, _ in enumerate(request.draftTexts)
            ),
        )


@pytest.fixture
def api(tmp_path: Path) -> tuple[TestClient, FrozenClock]:
    clock = FrozenClock(datetime(2026, 8, 12, 10, tzinfo=UTC))
    repository = SQLiteConversationRepository(tmp_path / "turn-api.sqlite3")
    app = create_app(
        settings=AppSettings(modelProvider=ModelProviderKind.MOCK),
        conversation_repository=repository,
        clock=clock,
        model_provider=DeterministicAPIProvider(),
    )
    return TestClient(app), clock


def create_conversation(client: TestClient) -> tuple[str, dict[str, Any]]:
    body = cast(dict[str, Any], client.post("/api/v1/conversations", json={}).json())
    conversation = cast(dict[str, Any], body["data"]["conversation"])
    return cast(str, conversation["conversationId"]), body


def send_first_answer(client: TestClient, conversation_id: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={
                "clientMessageId": "client-1",
                "baseRevision": 0,
                "content": "我的时间比较充足，喜欢安静陪在附近，也能接受日常打理。",
                "quickReplyId": None,
            },
        ).json(),
    )


def test_message_updates_profile_and_returns_one_dynamic_question(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, clock = api
    conversation_id, created = create_conversation(client)
    original_expiry = created["data"]["conversation"]["expiresAt"]
    clock.advance(timedelta(hours=1))

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-1",
            "baseRevision": 0,
            "content": "  我的时间比较充足，喜欢安静陪在附近，也能接受日常打理。  ",
            "quickReplyId": None,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conversation"]["revision"] == 1
    assert data["conversation"]["expiresAt"] != original_expiry
    assert data["nextQuestion"]["questionId"] == "confirm-species-allergy"
    assert data["recommendation"] is None
    assert data["assistantMessage"]["role"] == "ASSISTANT"
    assert {change["slotName"] for change in data["profileChanges"]} >= {
        "speciesScope",
        "currentTimeArrangement",
        "interactionRhythm",
    }


def test_duplicate_message_returns_first_data_without_a_second_write(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)
    payload = {
        "clientMessageId": "client-1",
        "baseRevision": 0,
        "content": "我的时间比较充足，喜欢安静陪在附近，也能接受日常打理。",
        "quickReplyId": None,
    }

    first = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json=payload
    )
    duplicate = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json=payload
    )

    assert first.status_code == duplicate.status_code == 200
    assert duplicate.json()["data"] == first.json()["data"]
    restored = client.get(f"/api/v1/conversations/{conversation_id}").json()["data"]
    assert restored["conversation"]["revision"] == 1
    assert len([item for item in restored["messages"] if item["role"] == "USER"]) == 1


def test_duplicate_old_quick_reply_replays_after_the_question_has_changed(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, created = create_conversation(client)
    old_reply = created["data"]["nextQuestion"]["quickReplies"][0]
    payload = {
        "clientMessageId": "client-1",
        "baseRevision": 0,
        "content": "我的时间比较充足，喜欢安静陪在附近，也能接受日常打理。",
        "quickReplyId": old_reply,
    }

    first = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json=payload
    )
    duplicate = client.post(
        f"/api/v1/conversations/{conversation_id}/messages", json=payload
    )

    assert first.status_code == duplicate.status_code == 200
    assert first.json()["data"]["nextQuestion"]["questionId"] == (
        "confirm-species-allergy"
    )
    assert duplicate.json()["data"] == first.json()["data"]

def test_stale_revision_returns_conflict_without_changing_state(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 0,
            "content": "猫狗都不过敏。",
            "quickReplyId": None,
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVISION_CONFLICT"
    assert response.json()["error"]["details"] == {"currentRevision": 1}
    restored = client.get(f"/api/v1/conversations/{conversation_id}").json()["data"]
    assert restored["conversation"]["revision"] == 1


def test_second_answer_synchronously_returns_a_public_recommendation(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conversation"]["revision"] == 2
    assert data["conversation"]["stage"] == "RECOMMENDED"
    assert data["nextQuestion"] is None
    assert data["recommendation"]["directions"]
    assert "internalScore" not in response.text


def test_recommendation_is_explained_and_safety_reviewed_before_commit(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )

    assert response.status_code == 200
    recommendation = response.json()["data"]["recommendation"]
    expected_subjects = [
        *(item["directionId"] for item in recommendation["directions"]),
        *(item["petId"] for item in recommendation["pets"]),
    ]
    assert recommendation["aiNarrative"]["intro"] == (
        "我把这次更值得认识的方向和伙伴整理好了。"
    )
    assert [
        item["subjectId"] for item in recommendation["aiNarrative"]["items"]
    ] == expected_subjects


@pytest.mark.parametrize(
    "provider",
    [InvalidExplanationProvider(), RejectedSafetyProvider()],
)
def test_invalid_or_unreviewed_explanation_rolls_back_the_whole_turn(
    tmp_path: Path,
    provider: DeterministicAPIProvider,
) -> None:
    clock = FrozenClock(datetime(2026, 8, 12, 10, tzinfo=UTC))
    app = create_app(
        settings=AppSettings(modelProvider=ModelProviderKind.MOCK),
        conversation_repository=SQLiteConversationRepository(
            tmp_path / "narrative-rollback.sqlite3"
        ),
        clock=clock,
        model_provider=provider,
    )
    client = TestClient(app)
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)
    before = client.get(f"/api/v1/conversations/{conversation_id}").json()["data"]

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "MODEL_INVALID_RESPONSE"
    after = client.get(f"/api/v1/conversations/{conversation_id}").json()["data"]
    assert after == before


def test_complete_safety_replacements_are_used_without_changing_candidates(
    tmp_path: Path,
) -> None:
    clock = FrozenClock(datetime(2026, 8, 12, 10, tzinfo=UTC))
    app = create_app(
        settings=AppSettings(modelProvider=ModelProviderKind.MOCK),
        conversation_repository=SQLiteConversationRepository(
            tmp_path / "narrative-replacement.sqlite3"
        ),
        clock=clock,
        model_provider=ReplacedSafetyProvider(),
    )
    client = TestClient(app)
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )

    assert response.status_code == 200
    recommendation = response.json()["data"]["recommendation"]
    assert recommendation["aiNarrative"]["intro"] == "安全版本1"
    assert all(
        item["text"].startswith("安全版本")
        for item in recommendation["aiNarrative"]["items"]
    )
    assert response.json()["data"]["warnings"] == ["已改为谨慎表达"]


def test_invalid_quick_reply_is_rejected_without_a_write(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-1",
            "baseRevision": 0,
            "content": "随便选一个。",
            "quickReplyId": "不存在的选项",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_QUICK_REPLY"
    restored = client.get(f"/api/v1/conversations/{conversation_id}").json()["data"]
    assert restored["conversation"]["revision"] == 0


@pytest.mark.parametrize("content", ["", "   ", "好" * 2001])
def test_message_content_is_validated_at_the_api_boundary(
    api: tuple[TestClient, FrozenClock], content: str
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-1",
            "baseRevision": 0,
            "content": content,
            "quickReplyId": None,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_profile_patch_recalculates_and_returns_changes(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)
    send_first_answer(client, conversation_id)
    client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )

    response = client.patch(
        f"/api/v1/conversations/{conversation_id}/profile",
        json={
            "baseRevision": 2,
            "updates": {
                "interactionRhythm": {
                    "value": "HIGH",
                    "constraintStrength": "PREFERENCE",
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conversation"]["revision"] == 3
    assert data["conversation"]["profileSummary"]["interactionRhythm"] == {
        "value": "HIGH",
        "status": "CONFIRMED",
    }
    assert data["profileChanges"][0]["slotName"] == "interactionRhythm"
    assert data["recommendation"] is not None
    assert data["recommendationChanges"]


def test_profile_patch_before_enough_information_returns_next_question(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)

    response = client.patch(
        f"/api/v1/conversations/{conversation_id}/profile",
        json={
            "baseRevision": 0,
            "updates": {
                "interactionRhythm": {
                    "value": "LOW_MEDIUM",
                    "constraintStrength": "PREFERENCE",
                }
            },
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conversation"]["revision"] == 1
    assert data["nextQuestion"]["questionId"] == "ask-current-time"
    assert data["recommendation"] is None
def test_profile_patch_rejects_a_non_public_slot(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)

    response = client.patch(
        f"/api/v1/conversations/{conversation_id}/profile",
        json={
            "baseRevision": 0,
            "updates": {
                "monthlyBudgetCny": {
                    "value": 800,
                    "constraintStrength": "HARD",
                }
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_recommendations_endpoint_distinguishes_not_ready_from_ready(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, _ = api
    conversation_id, _ = create_conversation(client)

    not_ready = client.get(
        f"/api/v1/conversations/{conversation_id}/recommendations"
    )
    assert not_ready.status_code == 409
    assert not_ready.json()["error"]["code"] == "RECOMMENDATION_NOT_READY"

    send_first_answer(client, conversation_id)
    client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-2",
            "baseRevision": 1,
            "content": "猫狗都不过敏。",
            "quickReplyId": "猫狗都不过敏",
        },
    )
    ready = client.get(f"/api/v1/conversations/{conversation_id}/recommendations")

    assert ready.status_code == 200
    assert ready.json()["data"]["recommendation"]["directions"]


def test_expired_message_returns_gone(
    api: tuple[TestClient, FrozenClock],
) -> None:
    client, clock = api
    conversation_id, _ = create_conversation(client)
    clock.advance(timedelta(hours=24))

    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={
            "clientMessageId": "client-1",
            "baseRevision": 0,
            "content": "我想继续聊。",
            "quickReplyId": None,
        },
    )

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "SESSION_EXPIRED"
