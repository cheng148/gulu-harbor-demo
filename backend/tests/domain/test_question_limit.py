from datetime import UTC, datetime

from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue
from app.domain.questions import QuestionImpact, select_next_question

NOW = datetime(2026, 8, 9, tzinfo=UTC)


def confirmed[T](value: T) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def allergy_confirmed_profile() -> PetPreferenceProfile:
    return PetPreferenceProfile(allergySpecies=confirmed(("NONE",)))


def test_three_core_questions_stop_without_extra_impact() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
    )

    assert question is None


def test_top_two_member_change_can_trigger_the_one_extra_question() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        candidateImpact={
            "ask-direction-and-size": QuestionImpact.TOP_TWO_MEMBER_CHANGE,
        },
    )

    assert question is not None
    assert question.questionId == "ask-direction-and-size"
    assert question.isExtra is True


def test_important_level_change_can_trigger_the_one_extra_question() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        candidateImpact={
            "ask-coat-and-appearance": QuestionImpact.IMPORTANT_LEVEL_CHANGE,
        },
    )

    assert question is not None
    assert question.questionId == "ask-coat-and-appearance"
    assert question.isExtra is True


def test_top_two_reorder_does_not_trigger_the_extra_question() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        candidateImpact={
            "ask-direction-and-size": QuestionImpact.TOP_TWO_ORDER_ONLY,
        },
    )

    assert question is None


def test_backup_reorder_does_not_trigger_the_extra_question() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        candidateImpact={
            "ask-coat-and-appearance": QuestionImpact.BACKUP_ORDER_ONLY,
        },
    )

    assert question is None


def test_extra_question_cannot_be_used_twice() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        extraQuestionUsed=True,
        candidateImpact={
            "ask-direction-and-size": QuestionImpact.TOP_TWO_MEMBER_CHANGE,
        },
    )

    assert question is None


def test_allergy_is_confirmed_after_core_questions_before_recommendation() -> None:
    question = select_next_question(
        PetPreferenceProfile(),
        (),
        (),
        coreQuestionCount=3,
    )

    assert question is not None
    assert question.questionId == "confirm-species-allergy"
    assert question.isExtra is False
    assert "过敏" in question.prompt


def test_known_allergy_is_not_asked_again() -> None:
    question = select_next_question(
        allergy_confirmed_profile(),
        (),
        (),
        coreQuestionCount=3,
        questionHistory=("confirm-species-allergy",),
    )

    assert question is None
