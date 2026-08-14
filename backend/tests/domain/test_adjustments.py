from datetime import UTC, datetime

from app.domain.conflicts import accept_adjustment
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def test_explicit_willingness_records_one_gap_at_seventy_five_percent() -> None:
    result = accept_adjustment(
        PetPreferenceProfile(),
        slot_name="currentTimeArrangement",
        source_message_id="m-adjust",
        accepted_at=NOW,
    )

    assert result.profile.acceptedAdjustments.value == ("currentTimeArrangement",)
    assert result.profile.acceptedAdjustments.status is SlotStatus.CONFIRMED
    assert result.adjustment.slotName == "currentTimeArrangement"
    assert result.adjustment.scoreRatio == 0.75
    assert result.adjustment.condition == "用户明确愿意为这一项调整"


def test_accepting_one_gap_does_not_clear_another_conflict() -> None:
    profile = PetPreferenceProfile(
        companionshipDistance=SlotValue[str](
            value="CLOSE",
            status=SlotStatus.CONFLICTED,
            sourceMessageIds=("m-1", "m-2"),
            updatedAt=NOW,
        )
    )

    result = accept_adjustment(
        profile,
        slot_name="currentTimeArrangement",
        source_message_id="m-adjust",
        accepted_at=NOW,
    )

    assert result.profile.companionshipDistance.status is SlotStatus.CONFLICTED
    assert result.profile.acceptedAdjustments.value == ("currentTimeArrangement",)


def test_repeating_the_same_adjustment_does_not_duplicate_it() -> None:
    first = accept_adjustment(
        PetPreferenceProfile(),
        slot_name="currentTimeArrangement",
        source_message_id="m-adjust",
        accepted_at=NOW,
    )
    second = accept_adjustment(
        first.profile,
        slot_name="currentTimeArrangement",
        source_message_id="m-adjust",
        accepted_at=NOW,
    )

    assert second.profile.acceptedAdjustments.value == ("currentTimeArrangement",)
