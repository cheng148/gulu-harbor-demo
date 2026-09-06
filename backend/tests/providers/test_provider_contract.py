from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.matching import MatchLevel
from app.domain.profile import SlotStatus
from app.domain.profile_merge import ProfileChange, ProfileDelta
from app.providers.base import (
    ModelProvider,
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    QuestionWordingRequest,
    QuestionWordingResponse,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    RecommendationFact,
    SafetyReviewRequest,
    SafetyReviewResponse,
)
from app.providers.mock import MockProvider, MockProviderFixtures, ProviderFixture


def provider() -> MockProvider:
    extraction_request = ProfileExtractionRequest(
        scenarioId="basic-dog",
        stepId="turn-1-extract",
        messageId="message-1",
        text="我工作日大约能陪它两小时。",
    )
    extraction_response = ProfileExtractionResponse(
        delta=ProfileDelta(
            sourceMessageId="message-1",
            changes=(
                ProfileChange(
                    slotName="dailyCompanionHours",
                    value=2.0,
                    status=SlotStatus.CONFIRMED,
                ),
            ),
        )
    )
    question_request = QuestionWordingRequest(
        scenarioId="basic-dog",
        stepId="turn-1-question",
        questionId="ask-current-time",
        prompt="平时一天大概能留出多少时间陪它？",
        quickReplies=("半小时左右", "1—2小时", "2小时以上"),
    )
    question_response = QuestionWordingResponse(
        questionId="ask-current-time",
        text="平时一天，你大概能留出多少时间陪它呀？",
        quickReplies=question_request.quickReplies,
    )
    explanation_request = RecommendationExplanationRequest(
        scenarioId="basic-dog",
        stepId="turn-4-explain",
        facts=(
            RecommendationFact(
                subjectId="pet-doubao",
                matchLevel=MatchLevel.HIGH,
                fitReasons=("互动节奏接近",),
                tradeoffs=("需要规律梳毛",),
                mismatchPoints=(),
            ),
        ),
        pendingItems=(),
    )
    explanation_response = RecommendationExplanationResponse(
        intro="先来认识一下这位可能合拍的小伙伴。",
        items=("豆包和你期待的互动节奏比较接近，也需要你接受规律梳毛。",),
    )
    safety_request = SafetyReviewRequest(
        scenarioId="basic-dog",
        stepId="turn-4-safety",
        draftTexts=explanation_response.items,
    )
    safety_response = SafetyReviewResponse(isApproved=True)

    return MockProvider(
        MockProviderFixtures(
            profileExtractions=(
                ProviderFixture(
                    request=extraction_request, response=extraction_response
                ),
            ),
            questionWordings=(
                ProviderFixture(request=question_request, response=question_response),
            ),
            recommendationExplanations=(
                ProviderFixture(
                    request=explanation_request, response=explanation_response
                ),
            ),
            safetyReviews=(
                ProviderFixture(request=safety_request, response=safety_response),
            ),
        )
    )


def test_mock_implements_the_same_four_operation_contract_as_real_providers() -> None:
    mock = provider()

    assert isinstance(mock, ModelProvider)
    assert (
        mock.extract_profile(mock.fixtures.profileExtractions[0].request)
        == mock.fixtures.profileExtractions[0].response
    )
    assert (
        mock.phrase_question(mock.fixtures.questionWordings[0].request)
        == mock.fixtures.questionWordings[0].response
    )
    assert (
        mock.explain_recommendation(mock.fixtures.recommendationExplanations[0].request)
        == mock.fixtures.recommendationExplanations[0].response
    )
    assert (
        mock.review_safety(mock.fixtures.safetyReviews[0].request)
        == mock.fixtures.safetyReviews[0].response
    )


def test_provider_output_schemas_reject_extra_or_malformed_model_data() -> None:
    with pytest.raises(ValidationError):
        QuestionWordingResponse.model_validate(
            {
                "questionId": "ask-current-time",
                "text": "",
                "quickReplies": [],
                "modelThoughts": "must never cross the boundary",
            }
        )

    with pytest.raises(ValidationError):
        SafetyReviewResponse.model_validate(
            {
                "isApproved": False,
                "flags": ["需要更谨慎的表达"],
                "safeReplacementTexts": [""],
            }
        )


def test_question_wording_cannot_change_the_selected_question() -> None:
    mock = provider()
    fixture = mock.fixtures.questionWordings[0]

    assert fixture.response.questionId == fixture.request.questionId
