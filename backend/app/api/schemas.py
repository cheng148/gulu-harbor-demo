from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.api.errors import ResponseMeta
from app.domain.matching import PublicRecommendation
from app.domain.profile import ConstraintStrength, SlotStatus
from app.domain.state import ConversationStage, RecommendationMode


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    clientLocale: Literal["zh-CN"] = "zh-CN"


class PublicSlotSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    value: str | float | bool | tuple[str, ...] | None = None
    status: SlotStatus


class PublicConversationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    conversationId: str = Field(min_length=1)
    revision: int = Field(ge=0)
    stage: ConversationStage
    recommendationMode: RecommendationMode
    profileSummary: dict[str, PublicSlotSummary]
    missingCriticalSlots: tuple[str, ...]
    activeBlockers: tuple[str, ...]
    conflicts: tuple[str, ...]
    lastActiveAt: datetime
    expiresAt: datetime


class PublicMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    messageId: str = Field(min_length=1)
    role: Literal["USER", "ASSISTANT"]
    content: str = Field(min_length=1)
    createdAt: datetime


class PublicQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    questionId: str = Field(min_length=1)
    text: str = Field(min_length=1)
    quickReplies: tuple[str, ...]


class CreateConversationData(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    conversation: PublicConversationSummary
    assistantMessage: PublicMessage
    nextQuestion: PublicQuestion


class CreateConversationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    data: CreateConversationData
    meta: ResponseMeta


class GetConversationData(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    conversation: PublicConversationSummary
    messages: tuple[PublicMessage, ...]
    currentQuestion: PublicQuestion | None
    recommendation: PublicRecommendation | None


class GetConversationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    data: GetConversationData
    meta: ResponseMeta


type PublicProfileSlotName = Literal[
    "speciesScope", "directionAndSizePreference", "agePreference",
    "coatAppearancePreference", "interactionRhythm", "companionshipDistance",
    "currentTimeArrangement", "ongoingInvestmentWillingness",
    "disturbanceTolerance", "allergySpecies", "absoluteBottomLines",
    "acceptedAdjustments", "priorityNotes", "volunteeredContext",
]
type PublicProfileValue = str | float | bool | tuple[str, ...]


class SendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    clientMessageId: str = Field(min_length=1, max_length=200)
    baseRevision: int = Field(ge=0)
    content: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]
    quickReplyId: str | None = Field(default=None, min_length=1)


class PublicProfileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    slotName: PublicProfileSlotName
    previousValue: PublicProfileValue | None = None
    value: PublicProfileValue | None = None
    status: SlotStatus


class PublicRecommendationChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    changeType: Literal[
        "ADDED", "REMOVED", "LEVEL_CHANGED", "STATUS_CHANGED", "UNCHANGED"
    ]
    subjectId: str | None = None
    detail: str = Field(min_length=1)


class TurnData(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    conversation: PublicConversationSummary
    assistantMessage: PublicMessage
    profileChanges: tuple[PublicProfileChange, ...]
    nextQuestion: PublicQuestion | None
    quickReplies: tuple[str, ...]
    recommendation: PublicRecommendation | None
    warnings: tuple[str, ...]
    recommendationChanges: tuple[PublicRecommendationChange, ...] = ()


class TurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    data: TurnData
    meta: ResponseMeta


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    value: PublicProfileValue
    constraintStrength: ConstraintStrength = ConstraintStrength.PREFERENCE


class PatchProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    baseRevision: int = Field(ge=0)
    updates: dict[PublicProfileSlotName, ProfileUpdate] = Field(min_length=1)


class RecommendationData(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    conversation: PublicConversationSummary
    recommendation: PublicRecommendation


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    data: RecommendationData
    meta: ResponseMeta
