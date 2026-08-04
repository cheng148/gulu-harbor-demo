from datetime import UTC, datetime

from app.domain.conflicts import detect_conflicts
from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
    YesNoUncertain,
)

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def confirmed[T](value: T, *, hard: bool = False, source: str = "m-1") -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=ConstraintStrength.HARD if hard else ConstraintStrength.UNSET,
        sourceMessageIds=(source,),
        updatedAt=NOW,
    )


def test_long_alone_time_conflicts_with_highly_affectionate_preference() -> None:
    profile = PetPreferenceProfile(
        aloneHours=confirmed(10, hard=True),
        activityPreference=confirmed("HIGHLY_AFFECTIONATE"),
    )

    conflicts = detect_conflicts(profile)

    assert conflicts[0].code == "ALONE_TIME_VS_COMPANIONSHIP"
    assert conflicts[0].slotNames == ("aloneHours", "activityPreference")
    assert conflicts[0].questionId == "clarify-alone-vs-companionship"


def test_explicit_slot_conflict_precedes_soft_preference_conflict() -> None:
    profile = PetPreferenceProfile(
        petAllowed=SlotValue[YesNoUncertain](
            value=YesNoUncertain.YES,
            status=SlotStatus.CONFLICTED,
            constraintStrength=ConstraintStrength.HARD,
            sourceMessageIds=("m-1", "m-3"),
            updatedAt=NOW,
        ),
        aloneHours=confirmed(10, hard=True, source="m-1"),
        activityPreference=confirmed("HIGHLY_AFFECTIONATE", source="m-2"),
    )

    conflicts = detect_conflicts(profile)

    assert [item.code for item in conflicts] == [
        "SLOT_VALUE_CONFLICT:petAllowed",
        "ALONE_TIME_VS_COMPANIONSHIP",
    ]


def test_conflict_order_is_deterministic() -> None:
    profile = PetPreferenceProfile(
        aloneHours=confirmed(10, hard=True),
        activityPreference=confirmed("HIGHLY_AFFECTIONATE"),
        dailyExerciseMinutes=confirmed(15, hard=True),
        speciesPreference=confirmed("HIGH_ENERGY_DOG"),
    )

    first = detect_conflicts(profile)
    second = detect_conflicts(profile)

    assert first == second
    assert [item.code for item in first] == [
        "EXERCISE_VS_HIGH_ENERGY_DOG",
        "ALONE_TIME_VS_COMPANIONSHIP",
    ]
