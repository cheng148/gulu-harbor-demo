from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.domain.conflicts import detect_conflicts
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


_CORE_SLOTS = (
    "currentTimeArrangement",
    "interactionRhythm",
    "companionshipDistance",
    "ongoingInvestmentWillingness",
    "disturbanceTolerance",
    "absoluteBottomLines",
)


def _missing_core_slots(profile: PetPreferenceProfile) -> tuple[str, ...]:
    return tuple(
        name
        for name in _CORE_SLOTS
        if getattr(profile, name).status
        in {SlotStatus.UNKNOWN, SlotStatus.INFERRED, SlotStatus.DECLINED}
    )


def _allergy_is_confirmed(profile: PetPreferenceProfile) -> bool:
    return profile.allergySpecies.status is SlotStatus.CONFIRMED


def assess_readiness(
    profile: PetPreferenceProfile,
    *,
    requestDirect: bool = False,
    coreQuestionCount: int = 0,
    extraQuestionUsed: bool = False,
    importantUnknowns: tuple[str, ...] = (),
    recommendationStable: bool = False,
    allCandidatesExcluded: bool = False,
) -> ReadinessAssessment:
    conflicts = detect_conflicts(profile)
    if conflicts:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.CONTINUE_QUESTIONING,
            missingCriticalSlots=importantUnknowns,
            blockingCodes=tuple(item.code for item in conflicts),
        )

    if not _allergy_is_confirmed(profile):
        return ReadinessAssessment(
            outcome=ReadinessOutcome.CONTINUE_QUESTIONING,
            missingCriticalSlots=("allergySpecies",),
            blockingCodes=("ALLERGY_CONFIRMATION_REQUIRED",),
        )

    if allCandidatesExcluded:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.NOT_RECOMMENDED,
            missingCriticalSlots=(),
            blockingCodes=("NO_ELIGIBLE_CANDIDATES",),
        )

    if importantUnknowns and not extraQuestionUsed and not requestDirect:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.CONTINUE_QUESTIONING,
            missingCriticalSlots=importantUnknowns,
            blockingCodes=("EXTRA_QUESTION_REQUIRED",),
        )

    if requestDirect:
        if recommendationStable and not importantUnknowns:
            return ReadinessAssessment(
                outcome=ReadinessOutcome.FINAL,
                missingCriticalSlots=(),
                blockingCodes=(),
            )
        return ReadinessAssessment(
            outcome=ReadinessOutcome.PROVISIONAL,
            missingCriticalSlots=importantUnknowns,
            blockingCodes=(),
        )

    if importantUnknowns and extraQuestionUsed:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.PROVISIONAL,
            missingCriticalSlots=importantUnknowns,
            blockingCodes=(),
        )

    missing_core = _missing_core_slots(profile)
    if recommendationStable or coreQuestionCount >= 3 or not missing_core:
        return ReadinessAssessment(
            outcome=ReadinessOutcome.FINAL,
            missingCriticalSlots=(),
            blockingCodes=(),
        )

    return ReadinessAssessment(
        outcome=ReadinessOutcome.CONTINUE_QUESTIONING,
        missingCriticalSlots=missing_core,
        blockingCodes=(),
    )
