from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.profile import (
    AllergyLevel,
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    YesNoUncertain,
)


class ConstraintOutcome(StrEnum):
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    BLOCK_FINAL = "BLOCK_FINAL"
    EXCLUDE_CANDIDATE = "EXCLUDE_CANDIDATE"
    CLARIFY = "CLARIFY"


class ConstraintDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: ConstraintOutcome
    code: str
    reason: str
    affectedSlots: tuple[str, ...]


class CandidateRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidateId: str
    minimumExerciseMinutes: int = Field(ge=0)
    minimumMonthlyCostCny: int = Field(ge=0)
    minimumCompanionHours: float = Field(default=0, ge=0, le=24)
    maximumAloneHours: float = Field(default=24, ge=0, le=24)


def evaluate_session_constraints(
    profile: PetPreferenceProfile,
) -> tuple[ConstraintDecision, ...]:
    decisions: list[ConstraintDecision] = []

    if profile.petAllowed.status not in {SlotStatus.CONFIRMED, SlotStatus.DECLINED} or (
        profile.petAllowed.value is YesNoUncertain.UNCERTAIN
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.CLARIFY,
                code="PET_PERMISSION_UNKNOWN",
                reason="需要先确认住房或管理规定是否允许养宠。",
                affectedSlots=("petAllowed",),
            )
        )
    elif profile.petAllowed.value is YesNoUncertain.NO:
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.NOT_RECOMMENDED,
                code="PET_NOT_ALLOWED",
                reason="当前住房明确禁养，暂不建议进入选宠或购买流程。",
                affectedSlots=("petAllowed",),
            )
        )

    if profile.householdConsent.value is YesNoUncertain.NO:
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.NOT_RECOMMENDED,
                code="HOUSEHOLD_OPPOSED",
                reason="共同居住者明确反对，需要先取得一致。",
                affectedSlots=("householdConsent",),
            )
        )

    if profile.allergyLevel.value is AllergyLevel.SEVERE:
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.BLOCK_FINAL,
                code="SEVERE_ALLERGY_UNASSESSED",
                reason="严重过敏需要先由专业人员评估，不能承诺任何品种绝对不过敏。",
                affectedSlots=("allergyLevel",),
            )
        )
    elif profile.allergyLevel.value in {AllergyLevel.MILD, AllergyLevel.UNCERTAIN}:
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.CLARIFY,
                code="ALLERGY_NEEDS_CLARIFICATION",
                reason="需要了解实际接触反应，并建议咨询专业人员。",
                affectedSlots=("allergyLevel",),
            )
        )

    if profile.stableCarePlan.status is SlotStatus.CONFIRMED and not profile.stableCarePlan.value:
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.NOT_RECOMMENDED,
                code="NO_STABLE_CARE_PLAN",
                reason="当前没有稳定照护人或安排，暂不建议养宠。",
                affectedSlots=("stableCarePlan",),
            )
        )

    if (
        profile.emergencyBudgetReady.status is SlotStatus.CONFIRMED
        and not profile.emergencyBudgetReady.value
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.BLOCK_FINAL,
                code="EMERGENCY_BUDGET_NOT_READY",
                reason="可以给暂定方向，但正式建议前应准备突发医疗方案。",
                affectedSlots=("emergencyBudgetReady",),
            )
        )

    return tuple(decisions)


def evaluate_candidate_constraints(
    profile: PetPreferenceProfile,
    candidate: CandidateRequirements,
) -> tuple[ConstraintDecision, ...]:
    decisions: list[ConstraintDecision] = []

    exercise = profile.dailyExerciseMinutes
    if exercise.status is SlotStatus.CONFIRMED and (
        exercise.value is not None and exercise.value < candidate.minimumExerciseMinutes
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                code="EXERCISE_INSUFFICIENT",
                reason="候选的最低运动需求超过用户可稳定提供的时间。",
                affectedSlots=("dailyExerciseMinutes",),
            )
        )

    budget = profile.monthlyBudgetCny
    if (
        budget.status is SlotStatus.CONFIRMED
        and budget.constraintStrength is ConstraintStrength.HARD
        and budget.value is not None
        and budget.value < candidate.minimumMonthlyCostCny
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                code="BUDGET_TOO_LOW",
                reason="候选的月度基础成本下限超过已确认的硬预算。",
                affectedSlots=("monthlyBudgetCny",),
            )
        )

    companion = profile.dailyCompanionHours
    if companion.status is SlotStatus.CONFIRMED and (
        companion.value is not None and companion.value < candidate.minimumCompanionHours
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                code="COMPANIONSHIP_INSUFFICIENT",
                reason="候选需要的稳定陪伴时间超过用户可提供值。",
                affectedSlots=("dailyCompanionHours",),
            )
        )

    alone = profile.aloneHours
    if alone.status is SlotStatus.CONFIRMED and (
        alone.value is not None and alone.value > candidate.maximumAloneHours
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                code="ALONE_TIME_TOO_LONG",
                reason="候选可承受的独处时间短于用户的稳定日常安排。",
                affectedSlots=("aloneHours",),
            )
        )

    return tuple(decisions)
