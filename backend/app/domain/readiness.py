from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.domain.conflicts import detect_conflicts
from app.domain.constraints import ConstraintOutcome, evaluate_session_constraints
from app.domain.profile import PetPreferenceProfile, SlotStatus


class ReadinessOutcome(StrEnum):
    CONTINUE_QUESTIONING = "CONTINUE_QUESTIONING"
    PROVISIONAL = "PROVISIONAL"
    FINAL = "FINAL"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"


class ReadinessAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: ReadinessOutcome
    missingCriticalSlots: tuple[str, ...]
    blockingCodes: tuple[str, ...]


_REQUIRED_SLOTS = (
    "petAllowed",
    "householdConsent",
    "allergyLevel",
    "stableCarePlan",
    "dailyCompanionHours",
    "aloneHours",
    "dailyExerciseMinutes",
    "monthlyBudgetCny",
    "emergencyBudgetReady",
    "housingType",
    "spaceLevel",
    "householdMembers",
    "otherPets",
)
_BURDEN_SLOTS = (
    "sheddingTolerance",
    "noiseTolerance",
    "odorTolerance",
    "groomingTolerance",
)


def _missing_critical_slots(profile: PetPreferenceProfile) -> tuple[str, ...]:
    missing = [
        name
        for name in _REQUIRED_SLOTS
        if getattr(profile, name).status is not SlotStatus.CONFIRMED
    ]
    if not any(
        getattr(profile, name).status is SlotStatus.CONFIRMED for name in _BURDEN_SLOTS
    ):
        missing.append("burdenTolerance")
    return tuple(missing)


def assess_readiness(
    profile: PetPreferenceProfile,
    *,
    requestDirect: bool = False,
) -> ReadinessAssessment:
    decisions = evaluate_session_constraints(profile)
    conflicts = detect_conflicts(profile)
    missing = _missing_critical_slots(profile)

    not_recommended = tuple(
        item.code for item in decisions if item.outcome is ConstraintOutcome.NOT_RECOMMENDED
    )
    if not_recommended:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.NOT_RECOMMENDED,
            missingCriticalSlots=missing,
            blockingCodes=not_recommended,
        )

    blocking = tuple(
        item.code
        for item in decisions
        if item.outcome in {ConstraintOutcome.CLARIFY, ConstraintOutcome.BLOCK_FINAL}
        and item.code != "EMERGENCY_BUDGET_NOT_READY"
    )
    if conflicts:
        blocking = (*blocking, *(item.code for item in conflicts))
    if blocking:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.CONTINUE_QUESTIONING,
            missingCriticalSlots=missing,
            blockingCodes=blocking,
        )

    has_emergency_warning = any(
        item.code == "EMERGENCY_BUDGET_NOT_READY" for item in decisions
    )
    if missing or has_emergency_warning:
        outcome = (
            ReadinessOutcome.PROVISIONAL
            if requestDirect
            else ReadinessOutcome.CONTINUE_QUESTIONING
        )
        return ReadinessAssessment(
            outcome=outcome,
            missingCriticalSlots=missing,
            blockingCodes=(),
        )

    return ReadinessAssessment(
        outcome=ReadinessOutcome.FINAL,
        missingCriticalSlots=(),
        blockingCodes=(),
    )
