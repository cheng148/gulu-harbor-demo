from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.matching import PublicRecommendation
from app.domain.profile import PetPreferenceProfile


class ConversationStage(StrEnum):
    NEW = "NEW"
    DISCOVERING = "DISCOVERING"
    RESOLVING_CONFLICT = "RESOLVING_CONFLICT"
    READY_TO_MATCH = "READY_TO_MATCH"
    MATCHING = "MATCHING"
    RECOMMENDED = "RECOMMENDED"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    RESET = "RESET"


class RecommendationMode(StrEnum):
    NONE = "NONE"
    PROVISIONAL = "PROVISIONAL"
    FINAL = "FINAL"


class MessageRole(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class MessageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    messageId: str
    role: MessageRole
    content: str
    createdAt: datetime


class AcceptedAdjustment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slotName: str = Field(min_length=1)
    sourceMessageId: str = Field(min_length=1)
    acceptedAt: datetime
    scoreRatio: float = Field(default=0.75, ge=0.75, le=0.75)
    condition: str = Field(default="用户明确愿意为这一项调整", min_length=1)


class ConversationState(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    schemaVersion: str = "1.0"
    conversationId: str = Field(min_length=1)
    revision: int = Field(default=0, ge=0)
    stage: ConversationStage = ConversationStage.NEW
    recommendationMode: RecommendationMode = RecommendationMode.NONE
    messages: tuple[MessageRecord, ...] = ()
    profile: PetPreferenceProfile = Field(default_factory=PetPreferenceProfile)
    missingCriticalSlots: tuple[str, ...] = ()
    activeBlockers: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    questionHistory: tuple[str, ...] = ()
    coreQuestionCount: int = Field(default=0, ge=0, le=3)
    extraQuestionUsed: bool = False
    importantUnknowns: tuple[str, ...] = ()
    acceptedAdjustments: tuple[AcceptedAdjustment, ...] = ()
    consecutiveUnclearTurns: int = Field(default=0, ge=0)
    retrievedSourceIds: tuple[str, ...] = ()
    directionCandidates: tuple[str, ...] = ()
    petCandidateIds: tuple[str, ...] = ()
    recommendations: PublicRecommendation | None = None
    safetyFlags: tuple[str, ...] = ()
    createdAt: datetime
    lastActiveAt: datetime
    expiresAt: datetime

    @model_validator(mode="after")
    def validate_timeline(self) -> ConversationState:
        if self.lastActiveAt < self.createdAt:
            raise ValueError("last activity cannot precede creation")
        if self.expiresAt <= self.lastActiveAt:
            raise ValueError("expiry must be after last activity")
        return self
