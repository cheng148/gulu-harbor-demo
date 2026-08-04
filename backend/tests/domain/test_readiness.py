from datetime import UTC, datetime

from app.domain.profile import (
    AllergyLevel,
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
    YesNoUncertain,
)
from app.domain.readiness import ReadinessOutcome, assess_readiness

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def confirmed[T](value: T, *, hard: bool = False) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=ConstraintStrength.HARD if hard else ConstraintStrength.UNSET,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def final_ready_profile() -> PetPreferenceProfile:
    return PetPreferenceProfile(
        petAllowed=confirmed(YesNoUncertain.YES),
        householdConsent=confirmed(YesNoUncertain.YES),
        allergyLevel=confirmed(AllergyLevel.NONE),
        stableCarePlan=confirmed(True),
        dailyCompanionHours=confirmed(4.0),
        aloneHours=confirmed(6.0),
        dailyExerciseMinutes=confirmed(60),
        monthlyBudgetCny=confirmed(1000, hard=True),
        emergencyBudgetReady=confirmed(True),
        housingType=confirmed("APARTMENT"),
        spaceLevel=confirmed("MEDIUM"),
        householdMembers=confirmed(("ADULT",)),
        otherPets=confirmed(()),
        sheddingTolerance=confirmed("MEDIUM"),
    )


def test_complete_safe_profile_is_ready_for_final_recommendation() -> None:
    result = assess_readiness(final_ready_profile())

    assert result.outcome is ReadinessOutcome.FINAL
    assert result.missingCriticalSlots == ()


def test_direct_request_with_non_blocking_missing_data_is_provisional() -> None:
    profile = final_ready_profile().model_copy(
        update={"odorTolerance": SlotValue[str]()}
    )
    profile = profile.model_copy(update={"householdMembers": SlotValue[tuple[str, ...]]()})

    result = assess_readiness(profile, requestDirect=True)

    assert result.outcome is ReadinessOutcome.PROVISIONAL
    assert "householdMembers" in result.missingCriticalSlots


def test_direct_request_cannot_skip_unknown_pet_permission() -> None:
    result = assess_readiness(PetPreferenceProfile(), requestDirect=True)

    assert result.outcome is ReadinessOutcome.CONTINUE_QUESTIONING
    assert "PET_PERMISSION_UNKNOWN" in result.blockingCodes


def test_housing_ban_returns_not_recommended() -> None:
    profile = PetPreferenceProfile(petAllowed=confirmed(YesNoUncertain.NO, hard=True))

    result = assess_readiness(profile, requestDirect=True)

    assert result.outcome is ReadinessOutcome.NOT_RECOMMENDED


def test_severe_allergy_never_becomes_final_or_provisional() -> None:
    profile = final_ready_profile().model_copy(
        update={"allergyLevel": confirmed(AllergyLevel.SEVERE, hard=True)}
    )

    result = assess_readiness(profile, requestDirect=True)

    assert result.outcome is ReadinessOutcome.CONTINUE_QUESTIONING
    assert "SEVERE_ALLERGY_UNASSESSED" in result.blockingCodes
