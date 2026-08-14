from datetime import UTC, datetime

from app.domain.conflicts import detect_conflicts
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue
from app.domain.questions import (
    QuestionImpact,
    load_question_rules,
    select_next_question,
)

NOW = datetime(2026, 8, 9, tzinfo=UTC)


def confirmed[T](value: T) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def test_question_library_excludes_rejected_default_topics() -> None:
    rules = load_question_rules()
    targets = {slot for rule in rules for slot in rule.targetSlots}

    assert "petAllowed" not in targets
    assert "householdConsent" not in targets
    assert "monthlyBudgetCny" not in targets
    assert "householdMembers" not in targets


def test_initial_profile_starts_with_time_in_a_warm_plain_tone() -> None:
    question = select_next_question(PetPreferenceProfile(), (), ())

    assert question is not None
    assert question.questionId == "ask-current-time"
    assert question.targetSlots == ("currentTimeArrangement",)
    assert question.isExtra is False
    assert "普通工作日" in question.prompt


def test_known_time_moves_to_relationship_instead_of_repeating() -> None:
    profile = PetPreferenceProfile(
        currentTimeArrangement=confirmed("WORKDAY_ALONE_8_HOURS"),
    )

    question = select_next_question(profile, (), ())

    assert question is not None
    assert question.questionId == "ask-relationship-style"
    assert "currentTimeArrangement" not in question.targetSlots


def test_known_time_and_relationship_move_to_daily_burden() -> None:
    profile = PetPreferenceProfile(
        currentTimeArrangement=confirmed("WORKDAY_ALONE_8_HOURS"),
        interactionRhythm=confirmed("CALM"),
        companionshipDistance=confirmed("NEARBY"),
    )

    question = select_next_question(profile, (), ())

    assert question is not None
    assert question.questionId == "ask-daily-burden"


def test_candidate_impact_can_change_which_missing_core_question_is_more_valuable() -> None:
    impact = {
        "ask-current-time": QuestionImpact.BACKUP_ORDER_ONLY,
        "ask-relationship-style": QuestionImpact.TOP_TWO_MEMBER_CHANGE,
    }

    question = select_next_question(
        PetPreferenceProfile(),
        (),
        (),
        candidateImpact=impact,
    )

    assert question is not None
    assert question.questionId == "ask-relationship-style"


def test_important_profile_conflict_interrupts_a_core_question_once() -> None:
    profile = PetPreferenceProfile(
        interactionRhythm=SlotValue[str](
            value="ACTIVE",
            status=SlotStatus.CONFLICTED,
            sourceMessageIds=("m-1", "m-2"),
            updatedAt=NOW,
        )
    )

    question = select_next_question(profile, (), detect_conflicts(profile))

    assert question is not None
    assert question.questionId == "clarify-slot-interactionRhythm"
    assert question.isExtra is True


def test_question_selection_is_deterministic() -> None:
    profile = PetPreferenceProfile(currentTimeArrangement=confirmed("FLEXIBLE"))
    impact = {"ask-daily-burden": QuestionImpact.IMPORTANT_LEVEL_CHANGE}

    first = select_next_question(profile, (), (), candidateImpact=impact)
    second = select_next_question(profile, (), (), candidateImpact=impact)

    assert first == second
