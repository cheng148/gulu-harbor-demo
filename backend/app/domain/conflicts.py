from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue


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


def _source[SlotType](slot: SlotValue[SlotType]) -> str:
    return slot.sourceMessageIds[0] if slot.sourceMessageIds else ""


def detect_conflicts(profile: PetPreferenceProfile) -> tuple[DetectedConflict, ...]:
    conflicts: list[DetectedConflict] = []

    for slot_name in PetPreferenceProfile.model_fields:
        slot = getattr(profile, slot_name)
        if slot.status is SlotStatus.CONFLICTED:
            conflicts.append(
                DetectedConflict(
                    code=f"SLOT_VALUE_CONFLICT:{slot_name}",
                    slotNames=(slot_name,),
                    facts=("此前已确认一个值", "后来出现不同说法"),
                    impact="系统不能替你选择其中一个答案，必须先确认当前事实。",
                    questionId=f"clarify-slot-{slot_name}",
                    question=f"关于{slot_name}，请确认现在应以哪个说法为准？",
                    riskPriority=0,
                    firstSourceMessageId=_source(slot),
                )
            )

    if (
        profile.dailyExerciseMinutes.value is not None
        and profile.dailyExerciseMinutes.value < 30
        and profile.speciesPreference.value == "HIGH_ENERGY_DOG"
    ):
        conflicts.append(
            DetectedConflict(
                code="EXERCISE_VS_HIGH_ENERGY_DOG",
                slotNames=("dailyExerciseMinutes", "speciesPreference"),
                facts=("每天可提供运动少于30分钟", "偏好高运动需求犬"),
                impact="这类犬的基本运动需求可能长期无法满足。",
                questionId="clarify-exercise-vs-high-energy-dog",
                question="你更愿意增加稳定运动时间，还是调整宠物方向？",
                riskPriority=10,
                firstSourceMessageId=_source(profile.dailyExerciseMinutes),
            )
        )

    if profile.aloneHours.value is not None and (
        profile.aloneHours.value >= 8
        and profile.activityPreference.value == "HIGHLY_AFFECTIONATE"
    ):
        conflicts.append(
            DetectedConflict(
                code="ALONE_TIME_VS_COMPANIONSHIP",
                slotNames=("aloneHours", "activityPreference"),
                facts=("宠物每天需长期独处", "偏好高度黏人的宠物"),
                impact="高度依赖陪伴的个体可能因长期独处出现明显压力。",
                questionId="clarify-alone-vs-companionship",
                question="你能调整独处安排，还是愿意优先考虑更能独处的方向？",
                riskPriority=20,
                firstSourceMessageId=_source(profile.aloneHours),
            )
        )

    return tuple(
        sorted(
            conflicts,
            key=lambda item: (item.riskPriority, item.firstSourceMessageId, item.code),
        )
    )
