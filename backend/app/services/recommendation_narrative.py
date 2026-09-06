from __future__ import annotations

from app.domain.matching import (
    PublicAINarrative,
    PublicAINarrativeItem,
    PublicRecommendation,
)
from app.providers.base import (
    ModelProvider,
    RecommendationExplanationRequest,
    RecommendationExplanationResponse,
    RecommendationFact,
    SafetyReviewRequest,
    SafetyReviewResponse,
    validate_recommendation_explanation_response,
    validate_safety_review_response,
)


def add_safe_ai_narrative(
    recommendation: PublicRecommendation,
    provider: ModelProvider,
    *,
    scenario_id: str,
    step_id: str,
) -> tuple[PublicRecommendation, tuple[str, ...]]:
    facts = tuple(
        RecommendationFact(
            subjectId=item.directionId,
            matchLevel=item.matchLevel,
            fitReasons=item.suitableReasons,
            tradeoffs=item.tradeoffs,
            mismatchPoints=item.mismatchPoints,
        )
        for item in recommendation.directions
    ) + tuple(
        RecommendationFact(
            subjectId=item.petId,
            matchLevel=item.matchLevel,
            fitReasons=item.suitableReasons,
            tradeoffs=item.tradeoffs,
            mismatchPoints=item.mismatchPoints,
        )
        for item in recommendation.pets
    )
    direction_pending = tuple(
        item for result in recommendation.directions for item in result.pendingItems
    )
    pet_pending = tuple(
        item for result in recommendation.pets for item in result.pendingItems
    )
    pending_items = tuple(dict.fromkeys((*direction_pending, *pet_pending)))
    explanation_request = RecommendationExplanationRequest(
        scenarioId=scenario_id,
        stepId=f"{step_id}:explain",
        facts=facts,
        pendingItems=pending_items,
    )
    explanation = RecommendationExplanationResponse.model_validate(
        provider.explain_recommendation(explanation_request)
    )
    explanation = validate_recommendation_explanation_response(
        explanation_request, explanation
    )

    draft_texts = (explanation.intro, *explanation.items)
    safety_request = SafetyReviewRequest(
        scenarioId=scenario_id,
        stepId=f"{step_id}:safety",
        draftTexts=draft_texts,
    )
    review = SafetyReviewResponse.model_validate(provider.review_safety(safety_request))
    review = validate_safety_review_response(safety_request, review)
    safe_texts = draft_texts if review.isApproved else review.safeReplacementTexts

    narrative = PublicAINarrative(
        intro=safe_texts[0],
        items=tuple(
            PublicAINarrativeItem(subjectId=fact.subjectId, text=text)
            for fact, text in zip(facts, safe_texts[1:], strict=True)
        ),
    )
    return recommendation.model_copy(update={"aiNarrative": narrative}), review.flags
