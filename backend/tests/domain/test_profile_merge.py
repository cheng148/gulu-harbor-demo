from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)
from app.domain.profile_merge import ProfileChange, ProfileDelta, merge_profile

NOW = datetime(2026, 8, 4, 10, tzinfo=UTC)


def test_single_text_for_a_multi_value_slot_is_normalized_to_one_item() -> None:
    """Real models may emit one selected token as a scalar instead of an array."""
    delta = ProfileDelta.model_validate(
        {
            "sourceMessageId": "message-live-1",
            "changes": [
                {
                    "slotName": "coatAppearancePreference",
                    "value": "SHORT_HAIR",
                    "status": "CONFIRMED",
                    "constraintStrength": "PREFERENCE",
                }
            ],
        }
    )

    assert delta.changes[0].value == ("SHORT_HAIR",)


def test_qualitative_cost_cannot_be_stored_as_a_numeric_monthly_budget() -> None:
    with pytest.raises(ValidationError):
        ProfileDelta.model_validate(
            {
                "sourceMessageId": "message-live-4",
                "changes": [
                    {
                        "slotName": "monthlyBudgetCny",
                        "value": "MEDIUM",
                        "status": "CONFIRMED",
                    }
                ],
            }
        )


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


def test_explicit_any_is_confirmed_neutral_not_unknown() -> None:
    delta = ProfileDelta(
        sourceMessageId="m-neutral",
        changes=(
            ProfileChange(
                slotName="directionAndSizePreference",
                value=("ANY",),
                status=SlotStatus.CONFIRMED,
            ),
        ),
    )

    result = merge_profile(PetPreferenceProfile(), delta, NOW)

    slot = result.profile.directionAndSizePreference
    assert slot.value == ("ANY",)
    assert slot.status is SlotStatus.CONFIRMED
    assert slot.sourceMessageIds == ("m-neutral",)


def test_declined_answer_stays_valueless_but_keeps_its_source() -> None:
    delta = ProfileDelta(
        sourceMessageId="m-declined",
        changes=(
            ProfileChange(
                slotName="companionshipDistance",
                value=None,
                status=SlotStatus.DECLINED,
            ),
        ),
    )

    result = merge_profile(PetPreferenceProfile(), delta, NOW)

    slot = result.profile.companionshipDistance
    assert slot.value is None
    assert slot.status is SlotStatus.DECLINED
    assert slot.sourceMessageIds == ("m-declined",)


def test_conflict_keeps_both_the_confirmed_and_incoming_sources() -> None:
    profile = PetPreferenceProfile(
        interactionRhythm=SlotValue[str](
            value="ACTIVE",
            status=SlotStatus.CONFIRMED,
            sourceMessageIds=("m-1",),
            updatedAt=NOW,
        )
    )
    delta = ProfileDelta(
        sourceMessageId="m-2",
        changes=(
            ProfileChange(
                slotName="interactionRhythm",
                value="CALM",
                status=SlotStatus.CONFIRMED,
            ),
        ),
    )

    result = merge_profile(profile, delta, NOW)

    assert result.profile.interactionRhythm.status is SlotStatus.CONFLICTED
    assert result.profile.interactionRhythm.value == "ACTIVE"
    assert result.profile.interactionRhythm.sourceMessageIds == ("m-1", "m-2")
    assert result.conflicts[0].incomingSourceMessageId == "m-2"


def test_explicit_edit_replaces_a_revised_slot() -> None:
    profile = PetPreferenceProfile(
        interactionRhythm=SlotValue[str](
            value="ACTIVE",
            status=SlotStatus.CONFIRMED,
            sourceMessageIds=("m-1",),
            updatedAt=NOW,
        )
    )
    delta = ProfileDelta(
        sourceMessageId="edit-1",
        changes=(
            ProfileChange(
                slotName="interactionRhythm",
                value="CALM",
                status=SlotStatus.CONFIRMED,
            ),
        ),
    )

    result = merge_profile(profile, delta, NOW, explicit_edit=True)

    assert result.profile.interactionRhythm.value == "CALM"
    assert result.profile.interactionRhythm.status is SlotStatus.CONFIRMED
    assert result.profile.interactionRhythm.sourceMessageIds == ("m-1", "edit-1")
