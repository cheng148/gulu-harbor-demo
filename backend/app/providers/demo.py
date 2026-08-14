from __future__ import annotations

from typing import ClassVar

from app.domain.profile import ConstraintStrength, SlotStatus
from app.domain.profile_merge import ProfileChange, ProfileDelta
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


class DemoMockProvider:
    """浏览器演示专用的确定性模型替身，不承载筛选、评分或追问决策。"""

    _changes_by_text: ClassVar[dict[str, tuple[ProfileChange, ...]]] = {
        "我想认识一只成年英国短毛猫，偏中等体型和短毛。": (
            ProfileChange(slotName="speciesScope", value=("CAT",), status=SlotStatus.CONFIRMED),
            ProfileChange(
                slotName="directionAndSizePreference",
                value=("cat-british-shorthair",),
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.PREFERENCE,
            ),
            ProfileChange(slotName="agePreference", value="ADULT", status=SlotStatus.CONFIRMED),
            ProfileChange(
                slotName="coatAppearancePreference",
                value=("SHORT_HAIR",),
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.PREFERENCE,
            ),
        ),
        "工作日能留出一些时间，希望活动量不用太高。": (
            ProfileChange(
                slotName="currentTimeArrangement",
                value="LOW_MEDIUM",
                status=SlotStatus.CONFIRMED,
            ),
        ),
        "我喜欢安静一点的互动，待在附近陪着就很好。": (
            ProfileChange(
                slotName="interactionRhythm",
                value="LOW_MEDIUM",
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.PREFERENCE,
            ),
            ProfileChange(
                slotName="companionshipDistance",
                value="NEARBY",
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.PREFERENCE,
            ),
        ),
        "我能接受规律梳毛和中等花费，没有绝对不能接受的日常负担。": (
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
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
        "猫狗都不过敏。": (
            ProfileChange(
                slotName="allergySpecies",
                value=(),
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
    }

    def extract_profile(
        self, request: ProfileExtractionRequest
    ) -> ProfileExtractionResponse:
        text = request.text.strip()
        return ProfileExtractionResponse(
            delta=ProfileDelta(
                sourceMessageId=request.messageId,
                changes=self._changes_by_text.get(text, ()),
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
            intro="我按刚才聊到的生活节奏，把方向和具体候选分别整理好了。",
            items=tuple(
                f"{fact.subjectId}：{fact.matchLevel.value}"
                for fact in request.facts
            ),
        )

    def review_safety(self, request: SafetyReviewRequest) -> SafetyReviewResponse:
        return SafetyReviewResponse(isApproved=True)
