from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SlotStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    INFERRED = "INFERRED"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CONFLICTED = "CONFLICTED"


class ConstraintStrength(StrEnum):
    HARD = "HARD"
    PREFERENCE = "PREFERENCE"
    UNSET = "UNSET"


class YesNoUncertain(StrEnum):
    YES = "YES"
    NO = "NO"
    UNCERTAIN = "UNCERTAIN"


class AllergyLevel(StrEnum):
    NONE = "NONE"
    MILD = "MILD"
    SEVERE = "SEVERE"
    UNCERTAIN = "UNCERTAIN"


class SlotValue[SlotType](BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, serialize_by_alias=True)

    value: SlotType | None = None
    status: SlotStatus = SlotStatus.UNKNOWN
    constraintStrength: ConstraintStrength = ConstraintStrength.UNSET
    sourceMessageIds: tuple[str, ...] = ()
    updatedAt: datetime | None = None

    @model_validator(mode="after")
    def validate_evidence(self) -> SlotValue[SlotType]:
        if self.status in {SlotStatus.UNKNOWN, SlotStatus.DECLINED} and self.value is not None:
            raise ValueError("unknown or declined slots cannot contain a value")
        if self.status in {
            SlotStatus.INFERRED,
            SlotStatus.CONFIRMED,
            SlotStatus.CONFLICTED,
        } and self.value is None:
            raise ValueError("evidenced slots must contain a value")
        if self.status in {SlotStatus.INFERRED, SlotStatus.CONFIRMED} and (
            not self.sourceMessageIds or self.updatedAt is None
        ):
            raise ValueError("evidenced slots require a source and update time")
        return self


def unknown_slot[SlotType]() -> SlotValue[SlotType]:
    return SlotValue[SlotType]()


class PetPreferenceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, serialize_by_alias=True)

    speciesPreference: SlotValue[str] = Field(default_factory=unknown_slot)
    housingType: SlotValue[str] = Field(default_factory=unknown_slot)
    petAllowed: SlotValue[YesNoUncertain] = Field(default_factory=unknown_slot)
    householdConsent: SlotValue[YesNoUncertain] = Field(default_factory=unknown_slot)
    spaceLevel: SlotValue[str] = Field(default_factory=unknown_slot)
    outdoorAccess: SlotValue[bool] = Field(default_factory=unknown_slot)
    householdMembers: SlotValue[tuple[str, ...]] = Field(default_factory=unknown_slot)
    childrenAgeRange: SlotValue[str] = Field(default_factory=unknown_slot)
    hasOlderAdults: SlotValue[bool] = Field(default_factory=unknown_slot)
    hasPregnantMember: SlotValue[bool] = Field(default_factory=unknown_slot)
    otherPets: SlotValue[tuple[str, ...]] = Field(default_factory=unknown_slot)
    allergyLevel: SlotValue[AllergyLevel] = Field(default_factory=unknown_slot)
    stableCarePlan: SlotValue[bool] = Field(default_factory=unknown_slot)
    dailyCompanionHours: SlotValue[float] = Field(default_factory=unknown_slot)
    dailyExerciseMinutes: SlotValue[int] = Field(default_factory=unknown_slot)
    aloneHours: SlotValue[float] = Field(default_factory=unknown_slot)
    experienceLevel: SlotValue[str] = Field(default_factory=unknown_slot)
    monthlyBudgetCny: SlotValue[int] = Field(default_factory=unknown_slot)
    emergencyBudgetReady: SlotValue[bool] = Field(default_factory=unknown_slot)
    sheddingTolerance: SlotValue[str] = Field(default_factory=unknown_slot)
    noiseTolerance: SlotValue[str] = Field(default_factory=unknown_slot)
    odorTolerance: SlotValue[str] = Field(default_factory=unknown_slot)
    groomingTolerance: SlotValue[str] = Field(default_factory=unknown_slot)
    activityPreference: SlotValue[str] = Field(default_factory=unknown_slot)
    sizePreference: SlotValue[str] = Field(default_factory=unknown_slot)
    agePreference: SlotValue[str] = Field(default_factory=unknown_slot)
    sourcePreference: SlotValue[str] = Field(default_factory=unknown_slot)
    appearancePreferences: SlotValue[tuple[str, ...]] = Field(default_factory=unknown_slot)
    priorityNotes: SlotValue[tuple[str, ...]] = Field(default_factory=unknown_slot)

    @model_validator(mode="after")
    def validate_numeric_ranges(self) -> PetPreferenceProfile:
        non_negative_slots = (
            self.dailyCompanionHours,
            self.dailyExerciseMinutes,
            self.aloneHours,
            self.monthlyBudgetCny,
        )
        if any(slot.value is not None and slot.value < 0 for slot in non_negative_slots):
            raise ValueError("time and budget values cannot be negative")
        return self
