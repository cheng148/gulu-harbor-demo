from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from app.domain.conflicts import DetectedConflict
from app.domain.constraints import ConstraintDecision
from app.domain.profile import PetPreferenceProfile, SlotStatus


class QuestionCategory(StrEnum):
    CONFLICT = "CONFLICT"
    CORE = "CORE"
    PREFERENCE = "PREFERENCE"
    ALLERGY = "ALLERGY"


class QuestionImpact(StrEnum):
    NONE = "NONE"
    BACKUP_ORDER_ONLY = "BACKUP_ORDER_ONLY"
    TOP_TWO_ORDER_ONLY = "TOP_TWO_ORDER_ONLY"
    IMPORTANT_LEVEL_CHANGE = "IMPORTANT_LEVEL_CHANGE"
    TOP_TWO_MEMBER_CHANGE = "TOP_TWO_MEMBER_CHANGE"


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
    isExtra: bool = False


_IMPACT_PRIORITY = {
    QuestionImpact.NONE: 0,
    QuestionImpact.BACKUP_ORDER_ONLY: 1,
    QuestionImpact.TOP_TWO_ORDER_ONLY: 2,
    QuestionImpact.IMPORTANT_LEVEL_CHANGE: 3,
    QuestionImpact.TOP_TWO_MEMBER_CHANGE: 4,
}
_EXTRA_QUESTION_IMPACTS = {
    QuestionImpact.IMPORTANT_LEVEL_CHANGE,
    QuestionImpact.TOP_TWO_MEMBER_CHANGE,
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


def _to_next_question(rule: QuestionRule, *, is_extra: bool = False) -> NextQuestion:
    return NextQuestion(
        questionId=rule.questionId,
        targetSlots=rule.targetSlots,
        category=rule.category,
        promptTemplateId=rule.promptTemplateId,
        prompt=rule.prompt,
        quickReplies=rule.quickReplies,
        isExtra=is_extra,
    )


def _select_by_impact(
    rules: list[QuestionRule],
    candidate_impact: dict[str, QuestionImpact],
) -> QuestionRule | None:
    if not rules:
        return None
    return min(
        rules,
        key=lambda rule: (
            -_IMPACT_PRIORITY[candidate_impact.get(rule.questionId, QuestionImpact.NONE)],
            rule.fixedOrder,
            rule.questionId,
        ),
    )


def select_next_question(
    profile: PetPreferenceProfile,
    blockers: tuple[ConstraintDecision, ...],
    conflicts: tuple[DetectedConflict, ...],
    *,
    questionHistory: tuple[str, ...] = (),
    coreQuestionCount: int = 0,
    extraQuestionUsed: bool = False,
    candidateImpact: dict[str, QuestionImpact] | None = None,
) -> NextQuestion | None:
    del blockers
    impact = candidateImpact or {}

    if conflicts and not extraQuestionUsed:
        conflict = conflicts[0]
        return NextQuestion(
            questionId=conflict.questionId,
            targetSlots=conflict.slotNames,
            category=QuestionCategory.CONFLICT,
            promptTemplateId=conflict.questionId,
            prompt=conflict.question,
            quickReplies=(),
            isExtra=True,
        )

    rules = load_question_rules()
    eligible_core = [
        rule
        for rule in rules
        if rule.category is QuestionCategory.CORE
        and rule.questionId not in questionHistory
        and _is_missing(profile, rule.targetSlots)
    ]
    if coreQuestionCount < 3 and eligible_core:
        selected = _select_by_impact(eligible_core, impact)
        return _to_next_question(selected) if selected is not None else None

    if not extraQuestionUsed:
        eligible_extra = [
            rule
            for rule in rules
            if rule.category is QuestionCategory.PREFERENCE
            and rule.questionId not in questionHistory
            and _is_missing(profile, rule.targetSlots)
            and impact.get(rule.questionId) in _EXTRA_QUESTION_IMPACTS
        ]
        selected_extra = _select_by_impact(eligible_extra, impact)
        if selected_extra is not None:
            return _to_next_question(selected_extra, is_extra=True)

    allergy_rule = next(
        rule for rule in rules if rule.category is QuestionCategory.ALLERGY
    )
    if (
        allergy_rule.questionId not in questionHistory
        and _is_missing(profile, allergy_rule.targetSlots)
    ):
        return _to_next_question(allergy_rule)

    return None
