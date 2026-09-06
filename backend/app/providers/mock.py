from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.providers.base import (
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    ProviderFailure,
    ProviderFailureCode,
    ProviderRequest,
    QuestionWordingRequest,
    QuestionWordingResponse,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    SafetyReviewRequest,
    SafetyReviewResponse,
    validate_profile_extraction_response,
    validate_question_wording_response,
    validate_recommendation_explanation_response,
    validate_safety_review_response,
)


class ProviderFixture[RequestT: BaseModel, ResponseT: BaseModel](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request: RequestT
    response: ResponseT


class MockProviderFixtures(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profileExtractions: tuple[
        ProviderFixture[ProfileExtractionRequest, ProfileExtractionResponse], ...
    ] = ()
    questionWordings: tuple[
        ProviderFixture[QuestionWordingRequest, QuestionWordingResponse], ...
    ] = ()
    recommendationExplanations: tuple[
        ProviderFixture[
            RecommendationExplanationRequest, RecommendationExplanationResponse
        ],
        ...,
    ] = ()
    safetyReviews: tuple[
        ProviderFixture[SafetyReviewRequest, SafetyReviewResponse], ...
    ] = ()


class MockProvider:
    """Exact-fixture model substitute; it contains no product decision logic."""

    def __init__(self, fixtures: MockProviderFixtures) -> None:
        self.fixtures = fixtures

    @staticmethod
    def _resolve[RequestT: ProviderRequest, ResponseT: BaseModel](
        request: RequestT,
        fixtures: tuple[ProviderFixture[RequestT, ResponseT], ...],
    ) -> ResponseT:
        request_json = request.model_dump_json()
        for fixture in fixtures:
            if fixture.request.model_dump_json() == request_json:
                return fixture.response.model_copy(deep=True)
        raise ProviderFailure(
            ProviderFailureCode.NO_FIXTURE,
            f"no deterministic fixture registered for {request.stepId}",
        )

    def extract_profile(
        self, request: ProfileExtractionRequest
    ) -> ProfileExtractionResponse:
        response = self._resolve(request, self.fixtures.profileExtractions)
        return validate_profile_extraction_response(request, response)

    def phrase_question(
        self, request: QuestionWordingRequest
    ) -> QuestionWordingResponse:
        response = self._resolve(request, self.fixtures.questionWordings)
        return validate_question_wording_response(request, response)

    def explain_recommendation(
        self, request: RecommendationExplanationRequest
    ) -> RecommendationExplanationResponse:
        response = self._resolve(request, self.fixtures.recommendationExplanations)
        return validate_recommendation_explanation_response(request, response)

    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        response = self._resolve(request, self.fixtures.safetyReviews)
        return validate_safety_review_response(request, response)
