from datetime import UTC, datetime

from app.domain.conflicts import detect_conflicts
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def conflicted[T](value: T, *, source: str = "m-1") -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFLICTED,
        sourceMessageIds=(source, "m-2"),
        updatedAt=NOW,
    )


def confirmed[T](value: T, *, source: str = "m-1") -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=(source,),
        updatedAt=NOW,
    )


def test_relationship_conflict_is_marked_for_clarification() -> None:
    profile = PetPreferenceProfile(interactionRhythm=conflicted("ACTIVE"))

    conflicts = detect_conflicts(profile)

    assert [item.code for item in conflicts] == [
        "SLOT_VALUE_CONFLICT:interactionRhythm"
    ]
    assert conflicts[0].questionId == "clarify-slot-interactionRhythm"


def test_volunteered_context_conflict_does_not_force_a_question() -> None:
    profile = PetPreferenceProfile(
        volunteeredContext=conflicted(("住房情况出现两个说法",)),
    )

    assert detect_conflicts(profile) == ()


def test_legacy_lifestyle_combination_is_a_gap_not_an_automatic_conflict() -> None:
    profile = PetPreferenceProfile(
        aloneHours=confirmed(10),
        activityPreference=confirmed("HIGHLY_AFFECTIONATE"),
    )

    assert detect_conflicts(profile) == ()


def test_allergy_and_bottom_line_conflicts_precede_preference_conflict() -> None:
    profile = PetPreferenceProfile(
        allergySpecies=conflicted(("CAT",)),
        absoluteBottomLines=conflicted(("SHEDDING_MAX:LOW",)),
        directionAndSizePreference=conflicted(("CORGI",)),
    )

    conflicts = detect_conflicts(profile)

    assert [item.code for item in conflicts] == [
        "SLOT_VALUE_CONFLICT:allergySpecies",
        "SLOT_VALUE_CONFLICT:absoluteBottomLines",
        "SLOT_VALUE_CONFLICT:directionAndSizePreference",
    ]


def test_conflict_order_is_deterministic() -> None:
    profile = PetPreferenceProfile(
        companionshipDistance=conflicted("CLOSE", source="m-3"),
        interactionRhythm=conflicted("ACTIVE", source="m-1"),
    )

    assert detect_conflicts(profile) == detect_conflicts(profile)
