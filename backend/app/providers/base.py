from __future__ import annotations

from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.matching import MatchLevel
from app.domain.profile import PetPreferenceProfile
from app.domain.profile_merge import ProfileDelta


class ProviderFailureCode(StrEnum):
    NO_FIXTURE = "NO_FIXTURE"
    TIMEOUT = "TIMEOUT"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    UNAVAILABLE = "UNAVAILABLE"


class ProviderFailure(RuntimeError):
    def __init__(self, code: ProviderFailureCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scenarioId: str = Field(min_length=1)
    stepId: str = Field(min_length=1)


class ProfileExtractionRequest(ProviderRequest):
    messageId: str = Field(min_length=1)
    text: str = Field(min_length=1)
    currentQuestionId: str | None = None
    currentProfile: PetPreferenceProfile = Field(default_factory=PetPreferenceProfile)


class ProfileExtractionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    delta: ProfileDelta
    isExplicitEdit: bool = False


class QuestionWordingRequest(ProviderRequest):
    questionId: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    quickReplies: tuple[str, ...] = ()


class QuestionWordingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    questionId: str = Field(min_length=1)
    text: str = Field(min_length=1)
    quickReplies: tuple[str, ...] = ()


class RecommendationFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subjectId: str = Field(min_length=1)
    matchLevel: MatchLevel
    fitReasons: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    mismatchPoints: tuple[str, ...]


class RecommendationExplanationRequest(ProviderRequest):
    facts: tuple[RecommendationFact, ...]
    pendingItems: tuple[str, ...]


class RecommendationExplanationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intro: str = Field(min_length=1)
    items: tuple[str, ...]


class SafetyReviewRequest(ProviderRequest):
    draftTexts: tuple[str, ...] = Field(min_length=1)


class SafetyReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    isApproved: bool
    flags: tuple[str, ...] = ()
    safeReplacementTexts: tuple[str, ...] = ()

    @model_validator(mode="after")
    def rejected_review_requires_a_reason(self) -> SafetyReviewResponse:
        if not self.isApproved and not self.flags:
            raise ValueError("a rejected safety review must include at least one flag")
        return self


@runtime_checkable
class ModelProvider(Protocol):
    def extract_profile(
        self, request: ProfileExtractionRequest
    ) -> ProfileExtractionResponse: ...

    def phrase_question(
        self, request: QuestionWordingRequest
    ) -> QuestionWordingResponse: ...

    def explain_recommendation(
        self, request: RecommendationExplanationRequest
    ) -> RecommendationExplanationResponse: ...

    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse: ...


def validate_profile_extraction_response(
    request: ProfileExtractionRequest, response: ProfileExtractionResponse
) -> ProfileExtractionResponse:
    """Keep model output from referring to a different user message."""
    if response.delta.sourceMessageId != request.messageId:
        raise ProviderFailure(
            ProviderFailureCode.INVALID_OUTPUT,
            "profile delta source does not match the input message",
        )
    canonical_values = {
        "speciesScope": {"CAT", "DOG"},
        "directionAndSizePreference": {
            "CAT-ADULT-LOCAL-MIX",
            "CAT-BRITISH-SHORTHAIR",
            "CAT-AMERICAN-SHORTHAIR",
            "CAT-RAGDOLL",
            "DOG-ADULT-LOCAL-MIX",
            "DOG-TOY-MINI-POODLE",
            "DOG-PEMBROKE-CORGI",
            "DOG-LABRADOR-RETRIEVER",
            "LARGE",
            "MEDIUM",
            "MEDIUM_LARGE",
            "MINI_SMALL_MEDIUM",
            "TOY_SMALL",
            "VARIABLE",
            "ANY",
        },
        "coatAppearancePreference": {
            "CURLY_HAIR",
            "SEMI_LONG_HAIR",
            "SHORT_HAIR",
            "VARIABLE",
            "ANY",
        },
        "interactionRhythm": {
            "HIGH",
            "LOW",
            "LOW_MEDIUM",
            "MEDIUM",
            "MEDIUM_HIGH",
            "VARIABLE",
            "ANY",
        },
        "companionshipDistance": {
            "ACTIVE_APPROACH",
            "CLOSE",
            "FOLLOWING",
            "INDEPENDENT",
            "NEARBY",
            "SAME_ROOM",
            "VARIABLE",
            "ANY",
        },
        "currentTimeArrangement": {
            "HIGH",
            "LOW",
            "LOW_MEDIUM",
            "MEDIUM",
            "MEDIUM_HIGH",
            "VARIABLE",
            "ANY",
        },
        "ongoingInvestmentWillingness": {
            "HIGH",
            "LOW",
            "MEDIUM",
            "MEDIUM_HIGH",
            "ANY",
        },
        "allergySpecies": {"CAT", "DOG"},
        "agePreference": {"ADULT", "YOUNG_ADULT", "ANY"},
    }
    for change in response.delta.changes:
        allowed = canonical_values.get(change.slotName)
        if allowed is None or change.value is None:
            continue
        values = change.value if isinstance(change.value, tuple) else (change.value,)
        if any(str(value).upper() not in allowed for value in values):
            raise ProviderFailure(
                ProviderFailureCode.INVALID_OUTPUT,
                f"profile delta used a noncanonical value for {change.slotName}",
            )
    return response


def validate_question_wording_response(
    request: QuestionWordingRequest, response: QuestionWordingResponse
) -> QuestionWordingResponse:
    """Keep wording providers from changing deterministic question decisions."""
    if response.questionId != request.questionId:
        raise ProviderFailure(
            ProviderFailureCode.INVALID_OUTPUT,
            "provider changed the question selected by deterministic rules",
        )
    if response.quickReplies != request.quickReplies:
        raise ProviderFailure(
            ProviderFailureCode.INVALID_OUTPUT,
            "provider changed deterministic quick replies",
        )
    return response
