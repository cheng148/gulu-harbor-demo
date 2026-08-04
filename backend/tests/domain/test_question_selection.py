from datetime import UTC, datetime

from app.domain.conflicts import detect_conflicts
from app.domain.constraints import evaluate_session_constraints
from app.domain.profile import (
    AllergyLevel,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
    YesNoUncertain,
)
from app.domain.questions import select_next_question

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def confirmed[T](value: T) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def test_unknown_permission_and_known_permission_choose_different_next_questions() -> None:
    uncertain = PetPreferenceProfile(petAllowed=confirmed(YesNoUncertain.UNCERTAIN))
    allowed = PetPreferenceProfile(
        petAllowed=confirmed(YesNoUncertain.YES),
        dailyCompanionHours=confirmed(1.0),
    )

    question_a = select_next_question(
        uncertain,
        evaluate_session_constraints(uncertain),
        (),
    )
    question_b = select_next_question(
        allowed,
        evaluate_session_constraints(allowed),
        (),
    )

    assert question_a is not None and question_a.questionId == "confirm-pet-permission"
    assert question_b is not None and question_b.questionId != question_a.questionId


def test_confirmed_housing_and_allergy_are_not_asked_again() -> None:
    profile = PetPreferenceProfile(
        petAllowed=confirmed(YesNoUncertain.YES),
        housingType=confirmed("SMALL_APARTMENT"),
        allergyLevel=confirmed(AllergyLevel.NONE),
    )

    question = select_next_question(
        profile,
        evaluate_session_constraints(profile),
        (),
    )

    assert question is not None
    assert "housingType" not in question.targetSlots
    assert "allergyLevel" not in question.targetSlots
    assert len(question.quickReplies) <= 5


def test_conflict_interrupts_a_planned_preference_question() -> None:
    profile = PetPreferenceProfile(
        petAllowed=confirmed(YesNoUncertain.YES),
        aloneHours=confirmed(10.0),
        activityPreference=confirmed("HIGHLY_AFFECTIONATE"),
    )

    question = select_next_question(profile, (), detect_conflicts(profile))

    assert question is not None
    assert question.questionId == "clarify-alone-vs-companionship"
    assert question.category == "CONFLICT"


def test_question_selection_is_stable_and_returns_one_question() -> None:
    profile = PetPreferenceProfile(petAllowed=confirmed(YesNoUncertain.YES))

    first = select_next_question(profile, (), (), candidateImpact={"confirm-allergy": 8})
    second = select_next_question(profile, (), (), candidateImpact={"confirm-allergy": 8})

    assert first == second
    assert first is not None and first.questionId == "confirm-allergy"
