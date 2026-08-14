from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.profile import (
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)
from app.domain.state import AcceptedAdjustment


class DetectedConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    slotNames: tuple[str, ...]
    facts: tuple[str, str]
    impact: str
    questionId: str
    question: str
    riskPriority: int
    firstSourceMessageId: str


class AdjustmentAcceptanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile: PetPreferenceProfile
    adjustment: AcceptedAdjustment


_IMPORTANT_CONFLICT_PRIORITIES = {
    "allergySpecies": 0,
    "absoluteBottomLines": 10,
    "speciesScope": 20,
    "directionAndSizePreference": 30,
    "agePreference": 40,
    "coatAppearancePreference": 50,
    "interactionRhythm": 60,
    "companionshipDistance": 70,
    "currentTimeArrangement": 80,
    "ongoingInvestmentWillingness": 90,
    "disturbanceTolerance": 100,
}
_ADJUSTABLE_GAP_SLOTS = {
    "interactionRhythm",
    "companionshipDistance",
    "currentTimeArrangement",
    "ongoingInvestmentWillingness",
    "disturbanceTolerance",
}


def _source[SlotType](slot: SlotValue[SlotType]) -> str:
    return slot.sourceMessageIds[0] if slot.sourceMessageIds else ""


def detect_conflicts(profile: PetPreferenceProfile) -> tuple[DetectedConflict, ...]:
    conflicts: list[DetectedConflict] = []

    for slot_name, priority in _IMPORTANT_CONFLICT_PRIORITIES.items():
        slot = getattr(profile, slot_name)
        if slot.status is not SlotStatus.CONFLICTED:
            continue
        conflicts.append(
            DetectedConflict(
                code=f"SLOT_VALUE_CONFLICT:{slot_name}",
                slotNames=(slot_name,),
                facts=("此前已确认一个值", "后来出现不同说法"),
                impact="这个差异可能改变推荐，需要先确认当前想法。",
                questionId=f"clarify-slot-{slot_name}",
                question=f"关于{slot_name}，现在更接近哪一种想法？",
                riskPriority=priority,
                firstSourceMessageId=_source(slot),
            )
        )

    return tuple(
        sorted(
            conflicts,
            key=lambda item: (item.riskPriority, item.firstSourceMessageId, item.code),
        )
    )


def accept_adjustment(
    profile: PetPreferenceProfile,
    *,
    slot_name: str,
    source_message_id: str,
    accepted_at: datetime,
) -> AdjustmentAcceptanceResult:
    if slot_name not in _ADJUSTABLE_GAP_SLOTS:
        raise ValueError("adjustment must reference a relationship or lifestyle gap")
    if not source_message_id:
        raise ValueError("adjustment requires a source message")

    current = profile.acceptedAdjustments
    accepted_slots = list(current.value or ())
    if slot_name not in accepted_slots:
        accepted_slots.append(slot_name)
    sources = list(current.sourceMessageIds)
    if source_message_id not in sources:
        sources.append(source_message_id)

    accepted_slot = SlotValue[tuple[str, ...]](
        value=tuple(accepted_slots),
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=tuple(sources),
        updatedAt=accepted_at,
    )
    profile_data = profile.model_dump(mode="python")
    profile_data["acceptedAdjustments"] = accepted_slot
    updated_profile = PetPreferenceProfile.model_validate(profile_data)
    adjustment = AcceptedAdjustment(
        slotName=slot_name,
        sourceMessageId=source_message_id,
        acceptedAt=accepted_at,
    )
    return AdjustmentAcceptanceResult(
        profile=updated_profile,
        adjustment=adjustment,
    )
