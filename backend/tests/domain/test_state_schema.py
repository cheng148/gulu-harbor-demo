from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)
from app.domain.state import AcceptedAdjustment, ConversationStage, ConversationState


def test_profile_serializes_explicit_unknown_slots() -> None:
    profile = PetPreferenceProfile()

    payload = profile.model_dump(mode="json")

    assert payload["petAllowed"] == {
        "value": None,
        "status": "UNKNOWN",
        "constraintStrength": "UNSET",
        "sourceMessageIds": [],
        "updatedAt": None,
    }
    assert payload["otherPets"]["value"] is None


def test_slot_rejects_a_value_without_evidence_status() -> None:
    with pytest.raises(ValidationError):
        SlotValue[str](value="YES")


def test_profile_rejects_negative_budget() -> None:
    with pytest.raises(ValidationError):
        PetPreferenceProfile(
            monthlyBudgetCny=SlotValue[int](
                value=-1,
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
                sourceMessageIds=("m-1",),
                updatedAt=datetime(2026, 8, 4, tzinfo=UTC),
            )
        )


def test_conversation_rejects_expiry_before_last_activity() -> None:
    now = datetime(2026, 8, 4, 10, tzinfo=UTC)

    with pytest.raises(ValidationError):
        ConversationState(
            conversationId="conversation-1",
            stage=ConversationStage.DISCOVERING,
            createdAt=now,
            lastActiveAt=now,
            expiresAt=now - timedelta(seconds=1),
        )


def test_conversation_state_round_trips_as_json() -> None:
    now = datetime(2026, 8, 4, 10, tzinfo=UTC)
    state = ConversationState(
        conversationId="conversation-1",
        stage=ConversationStage.DISCOVERING,
        createdAt=now,
        lastActiveAt=now,
        expiresAt=now + timedelta(hours=24),
    )

    restored = ConversationState.model_validate_json(state.model_dump_json())

    assert restored == state

def test_revised_profile_exposes_relationship_focused_slots_as_unknown() -> None:
    profile = PetPreferenceProfile()

    payload = profile.model_dump(mode="json")

    assert payload["speciesScope"]["status"] == "UNKNOWN"
    assert payload["directionAndSizePreference"]["status"] == "UNKNOWN"
    assert payload["interactionRhythm"]["status"] == "UNKNOWN"
    assert payload["companionshipDistance"]["status"] == "UNKNOWN"
    assert payload["currentTimeArrangement"]["status"] == "UNKNOWN"
    assert payload["ongoingInvestmentWillingness"]["status"] == "UNKNOWN"
    assert payload["disturbanceTolerance"]["status"] == "UNKNOWN"
    assert payload["allergySpecies"]["status"] == "UNKNOWN"
    assert payload["absoluteBottomLines"]["status"] == "UNKNOWN"
    assert payload["acceptedAdjustments"]["status"] == "UNKNOWN"
    assert payload["volunteeredContext"]["status"] == "UNKNOWN"


def test_conversation_tracks_revised_question_and_unknown_state() -> None:
    now = datetime(2026, 8, 4, 10, tzinfo=UTC)
    adjustment = AcceptedAdjustment(
        slotName="currentTimeArrangement",
        sourceMessageId="m-2",
        acceptedAt=now,
    )
    state = ConversationState(
        conversationId="conversation-1",
        stage=ConversationStage.DISCOVERING,
        coreQuestionCount=3,
        extraQuestionUsed=True,
        importantUnknowns=("companionshipDistance",),
        acceptedAdjustments=(adjustment,),
        createdAt=now,
        lastActiveAt=now,
        expiresAt=now + timedelta(hours=24),
    )

    restored = ConversationState.model_validate_json(state.model_dump_json())

    assert restored == state


def test_conversation_rejects_more_than_three_core_questions() -> None:
    now = datetime(2026, 8, 4, 10, tzinfo=UTC)

    with pytest.raises(ValidationError):
        ConversationState(
            conversationId="conversation-1",
            stage=ConversationStage.DISCOVERING,
            coreQuestionCount=4,
            createdAt=now,
            lastActiveAt=now,
            expiresAt=now + timedelta(hours=24),
        )


def test_accepted_adjustment_requires_a_specific_gap_and_source() -> None:
    now = datetime(2026, 8, 4, 10, tzinfo=UTC)

    with pytest.raises(ValidationError):
        AcceptedAdjustment(slotName="", sourceMessageId="m-2", acceptedAt=now)
