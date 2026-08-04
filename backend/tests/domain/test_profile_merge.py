from datetime import UTC, datetime

from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)
from app.domain.profile_merge import ProfileChange, ProfileDelta, merge_profile

NOW = datetime(2026, 8, 4, 10, tzinfo=UTC)


def confirmed_budget() -> PetPreferenceProfile:
    return PetPreferenceProfile(
        monthlyBudgetCny=SlotValue[int](
            value=800,
            status=SlotStatus.CONFIRMED,
            constraintStrength=ConstraintStrength.HARD,
            sourceMessageIds=("m-1",),
            updatedAt=NOW,
        )
    )


def test_inference_cannot_overwrite_a_confirmed_value() -> None:
    delta = ProfileDelta(
        sourceMessageId="m-2",
        changes=(
            ProfileChange(
                slotName="monthlyBudgetCny",
                value=1200,
                status=SlotStatus.INFERRED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
    )

    result = merge_profile(confirmed_budget(), delta, NOW)

    assert result.profile.monthlyBudgetCny.value == 800
    assert result.profile.monthlyBudgetCny.status is SlotStatus.CONFIRMED
    assert result.conflicts == ()


def test_different_direct_statement_marks_conflict_without_overwriting() -> None:
    delta = ProfileDelta(
        sourceMessageId="m-2",
        changes=(
            ProfileChange(
                slotName="monthlyBudgetCny",
                value=1200,
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
    )

    result = merge_profile(confirmed_budget(), delta, NOW)

    assert result.profile.monthlyBudgetCny.value == 800
    assert result.profile.monthlyBudgetCny.status is SlotStatus.CONFLICTED
    assert result.conflicts[0].slotName == "monthlyBudgetCny"
    assert result.conflicts[0].confirmedValue == 800
    assert result.conflicts[0].incomingValue == 1200


def test_explicit_profile_edit_replaces_old_value_and_closes_conflict() -> None:
    delta = ProfileDelta(
        sourceMessageId="edit-1",
        changes=(
            ProfileChange(
                slotName="monthlyBudgetCny",
                value=600,
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
    )

    result = merge_profile(confirmed_budget(), delta, NOW, explicit_edit=True)

    assert result.profile.monthlyBudgetCny.value == 600
    assert result.profile.monthlyBudgetCny.status is SlotStatus.CONFIRMED
    assert result.conflicts == ()


def test_replaying_same_message_is_idempotent() -> None:
    delta = ProfileDelta(
        sourceMessageId="m-1",
        changes=(
            ProfileChange(
                slotName="monthlyBudgetCny",
                value=800,
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
    )

    result = merge_profile(confirmed_budget(), delta, NOW)

    assert result.profile == confirmed_budget()
    assert result.conflicts == ()
