from __future__ import annotations

from datetime import datetime
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, model_validator

from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)

type ProfileSlotName = Literal[
    "speciesScope",
    "directionAndSizePreference",
    "coatAppearancePreference",
    "interactionRhythm",
    "companionshipDistance",
    "currentTimeArrangement",
    "ongoingInvestmentWillingness",
    "disturbanceTolerance",
    "allergySpecies",
    "absoluteBottomLines",
    "acceptedAdjustments",
    "volunteeredContext",
    "speciesPreference",
    "housingType",
    "petAllowed",
    "householdConsent",
    "spaceLevel",
    "outdoorAccess",
    "householdMembers",
    "childrenAgeRange",
    "hasOlderAdults",
    "hasPregnantMember",
    "otherPets",
    "allergyLevel",
    "stableCarePlan",
    "dailyCompanionHours",
    "dailyExerciseMinutes",
    "aloneHours",
    "experienceLevel",
    "monthlyBudgetCny",
    "emergencyBudgetReady",
    "sheddingTolerance",
    "noiseTolerance",
    "odorTolerance",
    "groomingTolerance",
    "activityPreference",
    "sizePreference",
    "agePreference",
    "sourcePreference",
    "appearancePreferences",
    "priorityNotes",
]
type ProfileValue = str | int | float | bool | tuple[str, ...]


class ProfileChange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slotName: ProfileSlotName
    value: ProfileValue | None = None
    status: SlotStatus
    constraintStrength: ConstraintStrength = ConstraintStrength.UNSET

    @model_validator(mode="after")
    def validate_delta_status(self) -> ProfileChange:
        allowed = {SlotStatus.INFERRED, SlotStatus.CONFIRMED, SlotStatus.DECLINED}
        if self.status not in allowed:
            raise ValueError("a profile delta must be inferred, confirmed, or declined")
        if self.status is SlotStatus.DECLINED and self.value is not None:
            raise ValueError("a declined change cannot contain a value")
        if self.status is not SlotStatus.DECLINED and self.value is None:
            raise ValueError("an evidenced change must contain a value")
        return self


class ProfileDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sourceMessageId: str
    changes: tuple[ProfileChange, ...]


class ProfileConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    slotName: ProfileSlotName
    confirmedValue: ProfileValue
    incomingValue: ProfileValue
    confirmedSourceMessageIds: tuple[str, ...]
    incomingSourceMessageId: str


class ProfileMergeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: PetPreferenceProfile
    conflicts: tuple[ProfileConflict, ...] = ()


def _with_source(existing: tuple[str, ...], source_message_id: str) -> tuple[str, ...]:
    if source_message_id in existing:
        return existing
    return (*existing, source_message_id)


def merge_profile(
    profile: PetPreferenceProfile,
    delta: ProfileDelta,
    updated_at: datetime,
    *,
    explicit_edit: bool = False,
) -> ProfileMergeResult:
    data = profile.model_dump(mode="python")
    conflicts: list[ProfileConflict] = []

    for change in delta.changes:
        current = cast(SlotValue[ProfileValue], getattr(profile, change.slotName))

        if (
            delta.sourceMessageId in current.sourceMessageIds
            and change.value == current.value
        ):
            continue
        if current.status is SlotStatus.CONFIRMED:
            if change.status is SlotStatus.INFERRED:
                continue
            if (
                not explicit_edit
                and change.value != current.value
                and change.value is not None
            ):
                conflicts.append(
                    ProfileConflict(
                        slotName=change.slotName,
                        confirmedValue=cast(ProfileValue, current.value),
                        incomingValue=change.value,
                        confirmedSourceMessageIds=current.sourceMessageIds,
                        incomingSourceMessageId=delta.sourceMessageId,
                    )
                )
                data[change.slotName] = current.model_copy(
                    update={
                        "status": SlotStatus.CONFLICTED,
                        "sourceMessageIds": _with_source(
                            current.sourceMessageIds, delta.sourceMessageId
                        ),
                        "updatedAt": updated_at,
                    }
                )
                continue

        data[change.slotName] = SlotValue[ProfileValue](
            value=change.value,
            status=change.status,
            constraintStrength=change.constraintStrength,
            sourceMessageIds=_with_source(
                current.sourceMessageIds, delta.sourceMessageId
            ),
            updatedAt=updated_at,
        )

    return ProfileMergeResult(
        profile=PetPreferenceProfile.model_validate(data),
        conflicts=tuple(conflicts),
    )
