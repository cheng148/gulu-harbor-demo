from __future__ import annotations

from app.agent.graph import build_agent_graph
from app.domain.profile import ConstraintStrength, PetPreferenceProfile, SlotStatus
from app.domain.profile_merge import ProfileChange
from app.domain.questions import NextQuestion, QuestionCategory, QuestionImpact
from app.domain.state import ConversationStage
from tests.fixtures.dialogues import (
    MESSAGE_ID,
    confirmed,
    conversation,
    graph_input,
    provider_for_turn,
    question,
)


def test_free_text_updates_profile_and_skips_core_topics_already_answered() -> None:
    state = conversation()
    message = "我工作日时间比较充足，喜欢经常互动，也能接受日常打理。"
    expected_question = question("confirm-species-allergy")
    provider = provider_for_turn(
        state,
        message_text=message,
        changes=(
            ProfileChange(
                slotName="currentTimeArrangement",
                value="HIGH",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="interactionRhythm",
                value="HIGH",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="companionshipDistance",
                value="NEARBY",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="ongoingInvestmentWillingness",
                value="HIGH",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="disturbanceTolerance",
                value=("SHEDDING_MEDIUM", "NOISE_MEDIUM"),
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="absoluteBottomLines",
                value=(),
                status=SlotStatus.CONFIRMED,
            ),
        ),
        next_question=expected_question,
    )

    result = build_agent_graph(provider).invoke(
        graph_input(state, message_text=message)
    )
    updated = result["conversation"]

    assert updated.profile.currentTimeArrangement.value == "HIGH"
    assert updated.profile.interactionRhythm.sourceMessageIds == (MESSAGE_ID,)
    assert result["nextQuestion"].questionId == "confirm-species-allergy"
    assert "ask-current-time" not in updated.questionHistory
    assert "ask-relationship-style" not in updated.questionHistory
    assert "ask-daily-burden" not in updated.questionHistory


def test_two_profiles_can_follow_different_dynamic_question_branches() -> None:
    short_time_state = conversation()
    short_time_message = "工作日时间比较少。"
    burden_question = question("ask-daily-burden")
    short_time_provider = provider_for_turn(
        short_time_state,
        message_text=short_time_message,
        changes=(
            ProfileChange(
                slotName="currentTimeArrangement",
                value="LOW",
                status=SlotStatus.CONFIRMED,
            ),
        ),
        next_question=burden_question,
    )
    short_time_result = build_agent_graph(short_time_provider).invoke(
        graph_input(
            short_time_state,
            message_text=short_time_message,
            candidate_impact={
                "ask-daily-burden": QuestionImpact.TOP_TWO_MEMBER_CHANGE,
            },
        )
    )

    independent_state = conversation()
    independent_message = "时间比较充足，但希望它不要太黏。"
    relationship_question = question("ask-relationship-style")
    independent_provider = provider_for_turn(
        independent_state,
        message_text=independent_message,
        changes=(
            ProfileChange(
                slotName="currentTimeArrangement",
                value="HIGH",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="companionshipDistance",
                value="INDEPENDENT",
                status=SlotStatus.CONFIRMED,
            ),
        ),
        next_question=relationship_question,
    )
    independent_result = build_agent_graph(independent_provider).invoke(
        graph_input(
            independent_state,
            message_text=independent_message,
            candidate_impact={
                "ask-relationship-style": QuestionImpact.TOP_TWO_MEMBER_CHANGE,
            },
        )
    )

    assert short_time_result["nextQuestion"].questionId == "ask-daily-burden"
    assert independent_result["nextQuestion"].questionId == "ask-relationship-style"


def test_conflicting_statement_is_preserved_and_clarified_before_other_questions() -> (
    None
):
    profile = PetPreferenceProfile(interactionRhythm=confirmed("HIGH"))
    state = conversation(profile=profile)
    message = "其实我现在更想要安静一点的陪伴。"
    conflict_question = NextQuestion(
        questionId="clarify-slot-interactionRhythm",
        targetSlots=("interactionRhythm",),
        category=QuestionCategory.CONFLICT,
        promptTemplateId="clarify-slot-interactionRhythm",
        prompt="关于interactionRhythm，现在更接近哪一种想法？",
        quickReplies=(),
        isExtra=True,
    )
    provider = provider_for_turn(
        state,
        message_text=message,
        changes=(
            ProfileChange(
                slotName="interactionRhythm",
                value="LOW_MEDIUM",
                status=SlotStatus.CONFIRMED,
            ),
        ),
        next_question=conflict_question,
    )

    result = build_agent_graph(provider).invoke(
        graph_input(state, message_text=message)
    )
    updated = result["conversation"]

    assert updated.stage is ConversationStage.RESOLVING_CONFLICT
    assert updated.profile.interactionRhythm.status is SlotStatus.CONFLICTED
    assert updated.profile.interactionRhythm.value == "HIGH"
    assert updated.conflicts == ("SLOT_VALUE_CONFLICT:interactionRhythm",)
    assert result["nextQuestion"].questionId == "clarify-slot-interactionRhythm"


def test_explicit_correction_wins_and_stale_model_inference_cannot_overwrite_it() -> (
    None
):
    profile = PetPreferenceProfile(
        interactionRhythm=confirmed("HIGH"),
        allergySpecies=confirmed(()),
    )
    state = conversation(profile=profile, core_question_count=3)
    message = "我改主意了，现在明确更喜欢安静陪伴。"
    provider = provider_for_turn(
        state,
        message_text=message,
        changes=(
            ProfileChange(
                slotName="interactionRhythm",
                value="LOW_MEDIUM",
                status=SlotStatus.CONFIRMED,
            ),
            ProfileChange(
                slotName="interactionRhythm",
                value="HIGH",
                status=SlotStatus.INFERRED,
            ),
        ),
        next_question=None,
        is_explicit_edit=True,
    )

    result = build_agent_graph(provider).invoke(
        graph_input(state, message_text=message)
    )
    updated = result["conversation"]

    assert updated.profile.interactionRhythm.value == "LOW_MEDIUM"
    assert updated.profile.interactionRhythm.status is SlotStatus.CONFIRMED
    assert updated.conflicts == ()
    assert updated.stage is ConversationStage.READY_TO_MATCH


def test_three_core_question_limit_stops_when_no_extra_question_is_justified() -> None:
    profile = PetPreferenceProfile(allergySpecies=confirmed(()))
    state = conversation(profile=profile, core_question_count=3)
    message = "暂时没有更多补充。"
    provider = provider_for_turn(
        state,
        message_text=message,
        changes=(),
        next_question=None,
    )

    result = build_agent_graph(provider).invoke(
        graph_input(state, message_text=message)
    )

    assert result["conversation"].stage is ConversationStage.READY_TO_MATCH
    assert result.get("nextQuestion") is None
    assert result["conversation"].coreQuestionCount == 3
    assert result["conversation"].extraQuestionUsed is False


def test_model_cannot_upgrade_an_ordinary_preference_into_a_hard_constraint() -> None:
    state = conversation()
    message = "我比较喜欢掉毛少一点。"
    expected_question = question("ask-current-time")
    provider = provider_for_turn(
        state,
        message_text=message,
        changes=(
            ProfileChange(
                slotName="coatAppearancePreference",
                value=("SHORT_HAIR",),
                status=SlotStatus.CONFIRMED,
                constraintStrength=ConstraintStrength.HARD,
            ),
        ),
        next_question=expected_question,
    )

    result = build_agent_graph(provider).invoke(
        graph_input(state, message_text=message)
    )

    assert (
        result["conversation"].profile.coatAppearancePreference.constraintStrength
        is ConstraintStrength.PREFERENCE
    )
