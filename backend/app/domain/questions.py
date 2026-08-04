from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from app.domain.conflicts import DetectedConflict
from app.domain.constraints import ConstraintDecision, ConstraintOutcome
from app.domain.profile import PetPreferenceProfile, SlotStatus


class QuestionCategory(StrEnum):
    BLOCKER = "BLOCKER"
    CONFLICT = "CONFLICT"
    CRITICAL = "CRITICAL"
    DISCRIMINATING = "DISCRIMINATING"
    PREFERENCE = "PREFERENCE"


class QuestionRule(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    questionId: str
    targetSlots: tuple[str, ...]
    category: QuestionCategory
    fixedOrder: int
    promptTemplateId: str
    prompt: str
    quickReplies: tuple[str, ...]


class NextQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    questionId: str
    targetSlots: tuple[str, ...]
    category: QuestionCategory
    promptTemplateId: str
    prompt: str
    quickReplies: tuple[str, ...]


_CATEGORY_PRIORITY = {
    QuestionCategory.BLOCKER: 0,
    QuestionCategory.CRITICAL: 2,
    QuestionCategory.DISCRIMINATING: 3,
    QuestionCategory.PREFERENCE: 4,
}


def load_question_rules() -> tuple[QuestionRule, ...]:
    path = Path(__file__).parent.parent / "data" / "question_rules.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TypeAdapter(tuple[QuestionRule, ...]).validate_python(payload)


def _is_missing(profile: PetPreferenceProfile, target_slots: tuple[str, ...]) -> bool:
    return any(
        getattr(profile, name).status in {SlotStatus.UNKNOWN, SlotStatus.INFERRED}
        for name in target_slots
    )


def select_next_question(
    profile: PetPreferenceProfile,
    blockers: tuple[ConstraintDecision, ...],
    conflicts: tuple[DetectedConflict, ...],
    *,
    questionHistory: tuple[str, ...] = (),
    candidateImpact: dict[str, int] | None = None,
) -> NextQuestion | None:
    if conflicts:
        conflict = conflicts[0]
        return NextQuestion(
            questionId=conflict.questionId,
            targetSlots=conflict.slotNames,
            category=QuestionCategory.CONFLICT,
            promptTemplateId=conflict.questionId,
            prompt=conflict.question,
            quickReplies=(),
        )

    clarification_slots = {
        slot
        for blocker in blockers
        if blocker.outcome is ConstraintOutcome.CLARIFY
        for slot in blocker.affectedSlots
    }
    impact = candidateImpact or {}
    eligible: list[QuestionRule] = []
    for rule in load_question_rules():
        if rule.questionId in questionHistory:
            continue
        if rule.category is QuestionCategory.BLOCKER:
            if clarification_slots.intersection(rule.targetSlots):
                eligible.append(rule)
        elif _is_missing(profile, rule.targetSlots):
            eligible.append(rule)

    if not eligible:
        return None
    selected = min(
        eligible,
        key=lambda rule: (
            _CATEGORY_PRIORITY[rule.category],
            -impact.get(rule.questionId, 0),
            rule.fixedOrder,
            rule.questionId,
        ),
    )
    return NextQuestion(
        questionId=selected.questionId,
        targetSlots=selected.targetSlots,
        category=selected.category,
        promptTemplateId=selected.promptTemplateId,
        prompt=selected.prompt,
        quickReplies=selected.quickReplies,
    )
