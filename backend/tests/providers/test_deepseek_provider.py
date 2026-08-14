from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.domain.profile_merge import ProfileDelta
from app.providers.base import (
    ModelProvider,
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    ProviderFailure,
    ProviderFailureCode,
    QuestionWordingRequest,
    QuestionWordingResponse,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    SafetyReviewRequest,
    SafetyReviewResponse,
)
from app.providers.deepseek import DeepSeekProvider


def _question_request() -> QuestionWordingRequest:
    return QuestionWordingRequest(
        scenarioId="basic-dog",
        stepId="turn-1-question",
        questionId="ask-current-time",
        prompt="平时一天大概能留出多少时间陪它？",
        quickReplies=("半小时左右", "1-2小时", "2小时以上"),
    )


def _completion(content: str | None, *, finish_reason: str = "stop") -> dict[str, Any]:
    return {
        "id": "completion-test",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content},
            }
        ],
        "created": 0,
        "model": "deepseek-v4-flash",
        "object": "chat.completion",
    }


def _provider(handler: Callable[[httpx.Request], httpx.Response]) -> DeepSeekProvider:
    return DeepSeekProvider(
        api_key=SecretStr("test-only-key"),
        base_url="https://api.deepseek.com/",
        model="deepseek-v4-flash",
        timeout_seconds=17.0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_deepseek_uses_json_output_and_explicitly_disables_thinking() -> None:
    request = _question_request()
    expected = QuestionWordingResponse(
        questionId=request.questionId,
        text="平时一天里，你大概能留出多少时间陪它呀？",
        quickReplies=request.quickReplies,
    )

    def handler(http_request: httpx.Request) -> httpx.Response:
        body = json.loads(http_request.content)
        assert http_request.url == "https://api.deepseek.com/chat/completions"
        assert http_request.headers["Authorization"] == "Bearer test-only-key"
        assert body["model"] == "deepseek-v4-flash"
        assert body["stream"] is False
        assert body["response_format"] == {"type": "json_object"}
        assert body["thinking"] == {"type": "disabled"}
        assert "JSON" in body["messages"][0]["content"]
        assert json.loads(body["messages"][1]["content"]) == request.model_dump(
            mode="json"
        )
        assert http_request.extensions["timeout"] == {
            "connect": 17.0,
            "read": 17.0,
            "write": 17.0,
            "pool": 17.0,
        }
        return httpx.Response(200, json=_completion(expected.model_dump_json()))

    provider = _provider(handler)

    assert isinstance(provider, ModelProvider)
    assert provider.phrase_question(request) == expected


def test_all_four_operations_return_the_shared_provider_schemas() -> None:
    extraction_request = ProfileExtractionRequest(
        scenarioId="basic-dog",
        stepId="turn-1-extract",
        messageId="message-1",
        text="我还不确定每天能陪多久。",
    )
    extraction_response = ProfileExtractionResponse(
        delta=ProfileDelta(sourceMessageId="message-1", changes=())
    )
    question_request = _question_request()
    question_response = QuestionWordingResponse(
        questionId=question_request.questionId,
        text="平时一天里，你大概能留出多少时间陪它呀？",
        quickReplies=question_request.quickReplies,
    )
    explanation_request = RecommendationExplanationRequest(
        scenarioId="basic-dog",
        stepId="turn-4-explain",
        facts=(),
        pendingItems=("dailyCompanionHours",),
    )
    explanation_response = RecommendationExplanationResponse(
        intro="我们先从目前知道的部分看看。",
        items=("陪伴时间还可以再确认一下。",),
    )
    safety_request = SafetyReviewRequest(
        scenarioId="basic-dog",
        stepId="turn-4-safety",
        draftTexts=explanation_response.items,
    )
    safety_response = SafetyReviewResponse(isApproved=True)
    contents = iter(
        [
            extraction_response.model_dump_json(),
            question_response.model_dump_json(),
            explanation_response.model_dump_json(),
            safety_response.model_dump_json(),
        ]
    )
    provider = _provider(
        lambda request: httpx.Response(
            200, json=_completion(next(contents)), request=request
        )
    )

    assert provider.extract_profile(extraction_request) == extraction_response
    assert provider.phrase_question(question_request) == question_response
    assert provider.explain_recommendation(explanation_request) == explanation_response
    assert provider.review_safety(safety_request) == safety_response


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_model_content_is_invalid(content: str | None) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_completion(content), request=request)

    provider = _provider(handler)

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT
    assert calls == 2


@pytest.mark.parametrize(
    ("content", "finish_reason"),
    [
        ("not-json", "stop"),
        ('{"questionId":"ask-current-time"}', "stop"),
        ('{"questionId":"ask-current-time"}', "length"),
    ],
)
def test_malformed_truncated_or_schema_invalid_content_is_rejected(
    content: str, finish_reason: str
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json=_completion(content, finish_reason=finish_reason),
            request=request,
        )

    provider = _provider(handler)

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT
    assert calls == 2


@pytest.mark.parametrize(
    ("first_content", "first_finish_reason"),
    [
        (None, "stop"),
        ("not-json", "stop"),
        ('{"questionId":"ask-current-time"}', "stop"),
        ('{"questionId":"ask-current-time"}', "length"),
    ],
)
def test_invalid_first_response_is_retried_once_then_can_succeed(
    first_content: str | None, first_finish_reason: str
) -> None:
    request = _question_request()
    expected = QuestionWordingResponse(
        questionId=request.questionId,
        text="平时一天里，你大概能留出多少时间陪它呢？",
        quickReplies=request.quickReplies,
    )
    calls = 0

    def handler(http_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            content = first_content
            finish_reason = first_finish_reason
        else:
            content = expected.model_dump_json()
            finish_reason = "stop"
        return httpx.Response(
            200,
            json=_completion(content, finish_reason=finish_reason),
            request=http_request,
        )

    provider = _provider(handler)

    assert provider.phrase_question(request) == expected
    assert calls == 2


def test_question_wording_cannot_change_deterministic_question_or_replies() -> None:
    content = QuestionWordingResponse(
        questionId="a-different-question",
        text="模型擅自换了问题",
        quickReplies=("模型擅自换了选项",),
    ).model_dump_json()
    provider = _provider(
        lambda request: httpx.Response(200, json=_completion(content), request=request)
    )

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT


def test_profile_delta_must_refer_to_the_input_message() -> None:
    request = ProfileExtractionRequest(
        scenarioId="basic-dog",
        stepId="turn-1-extract",
        messageId="message-1",
        text="我每天能陪它两小时。",
    )
    content = json.dumps(
        {
            "delta": {"sourceMessageId": "other-message", "changes": []},
            "isExplicitEdit": False,
        }
    )
    provider = _provider(
        lambda http_request: httpx.Response(
            200, json=_completion(content), request=http_request
        )
    )

    with pytest.raises(ProviderFailure) as error:
        provider.extract_profile(request)

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT


def test_timeout_is_reported_without_retrying() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("test timeout", request=request)

    provider = _provider(handler)

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.TIMEOUT
    assert calls == 1


def test_http_failure_is_unavailable_and_does_not_expose_secrets() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            401,
            json={"error": {"message": "bad test-only-key"}},
            request=request,
        )

    provider = _provider(handler)

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.UNAVAILABLE
    assert calls == 1
    assert "test-only-key" not in str(error.value)


def test_malformed_deepseek_envelope_is_invalid_output() -> None:
    provider = _provider(
        lambda request: httpx.Response(200, json={"choices": []}, request=request)
    )

    with pytest.raises(ProviderFailure) as error:
        provider.phrase_question(_question_request())

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT
