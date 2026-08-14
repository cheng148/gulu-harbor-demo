from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentGraphState
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue
from app.domain.profile_merge import (
    ProfileChange,
    ProfileDelta,
    ProfileSlotName,
    ProfileValue,
)
from app.domain.questions import (
    NextQuestion,
    QuestionCategory,
    QuestionImpact,
    QuestionRule,
    load_question_rules,
)
from app.domain.state import ConversationStage, ConversationState
from app.providers.base import (
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    QuestionWordingRequest,
    QuestionWordingResponse,
)
from app.providers.mock import MockProvider, MockProviderFixtures, ProviderFixture

NOW = datetime(2026, 8, 10, 9, tzinfo=UTC)
SCENARIO_ID = "question-flow"
TURN_ID = "turn-1"
MESSAGE_ID = "message-1"


def confirmed[ValueT](value: ValueT, *, source: str = "seed") -> SlotValue[ValueT]:
    return SlotValue[ValueT](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=(source,),
        updatedAt=NOW - timedelta(minutes=1),
    )


def conversation(
    *,
    profile: PetPreferenceProfile | None = None,
    stage: ConversationStage = ConversationStage.DISCOVERING,
    question_history: tuple[str, ...] = (),
    core_question_count: int = 0,
    extra_question_used: bool = False,
) -> ConversationState:
    return ConversationState(
        conversationId="conversation-1",
        stage=stage,
        profile=profile or PetPreferenceProfile(),
        questionHistory=question_history,
        coreQuestionCount=core_question_count,
        extraQuestionUsed=extra_question_used,
        createdAt=NOW - timedelta(minutes=2),
        lastActiveAt=NOW - timedelta(minutes=1),
        expiresAt=NOW + timedelta(hours=24),
    )


def question(question_id: str) -> NextQuestion:
    rule = next(
        item for item in load_question_rules() if item.questionId == question_id
    )
    return _to_next_question(rule)


def _to_next_question(rule: QuestionRule) -> NextQuestion:
    return NextQuestion(
        questionId=rule.questionId,
        targetSlots=rule.targetSlots,
        category=rule.category,
        promptTemplateId=rule.promptTemplateId,
        prompt=rule.prompt,
        quickReplies=rule.quickReplies,
    )


def provider_for_turn(
    state: ConversationState,
    *,
    message_text: str,
    changes: tuple[ProfileChange, ...],
    next_question: NextQuestion | None,
    is_explicit_edit: bool = False,
    scenario_id: str = SCENARIO_ID,
    turn_id: str = TURN_ID,
    message_id: str = MESSAGE_ID,
) -> MockProvider:
    extraction_request = ProfileExtractionRequest(
        scenarioId=scenario_id,
        stepId=f"{turn_id}:extract",
        messageId=message_id,
        text=message_text,
        currentQuestionId=(
            state.questionHistory[-1] if state.questionHistory else None
        ),
        currentProfile=state.profile,
    )
    extraction_response = ProfileExtractionResponse(
        delta=ProfileDelta(sourceMessageId=message_id, changes=changes),
        isExplicitEdit=is_explicit_edit,
    )
    question_fixtures: tuple[
        ProviderFixture[QuestionWordingRequest, QuestionWordingResponse], ...
    ] = ()
    if next_question is not None:
        wording_request = QuestionWordingRequest(
            scenarioId=scenario_id,
            stepId=f"{turn_id}:question",
            questionId=next_question.questionId,
            prompt=next_question.prompt,
            quickReplies=next_question.quickReplies,
        )
        wording_response = QuestionWordingResponse(
            questionId=next_question.questionId,
            text=f"自然问法：{next_question.prompt}",
            quickReplies=next_question.quickReplies,
        )
        question_fixtures = (
            ProviderFixture(request=wording_request, response=wording_response),
        )

    return MockProvider(
        MockProviderFixtures(
            profileExtractions=(
                ProviderFixture(
                    request=extraction_request,
                    response=extraction_response,
                ),
            ),
            questionWordings=question_fixtures,
        )
    )


def graph_input(
    state: ConversationState,
    *,
    message_text: str,
    candidate_impact: dict[str, QuestionImpact] | None = None,
    scenario_id: str = SCENARIO_ID,
    turn_id: str = TURN_ID,
    message_id: str = MESSAGE_ID,
    occurred_at: datetime = NOW,
) -> AgentGraphState:
    return {
        "conversation": state,
        "scenarioId": scenario_id,
        "turnId": turn_id,
        "messageId": message_id,
        "messageText": message_text,
        "occurredAt": occurred_at,
        "candidateImpact": candidate_impact or {},
        "trace": (),
    }


@dataclass(frozen=True)
class DialogueTurn:
    text: str
    changes: tuple[ProfileChange, ...]
    expectedQuestionId: str | None
    isExplicitEdit: bool = False
    candidateImpact: dict[str, QuestionImpact] = field(default_factory=dict)


@dataclass(frozen=True)
class DialogueScenario:
    scenarioId: str
    turns: tuple[DialogueTurn, ...]


@dataclass(frozen=True)
class DialogueRunResult:
    scenarioId: str
    turnCount: int
    askedQuestionIds: tuple[str, ...]
    stageHistory: tuple[ConversationStage, ...]
    conflictCodesSeen: tuple[str, ...]
    finalState: ConversationState


def _expected_question(question_id: str | None) -> NextQuestion | None:
    if question_id is None:
        return None
    if question_id.startswith("clarify-slot-"):
        slot_name = question_id.removeprefix("clarify-slot-")
        return NextQuestion(
            questionId=question_id,
            targetSlots=(slot_name,),
            category=QuestionCategory.CONFLICT,
            promptTemplateId=question_id,
            prompt=f"关于{slot_name}，现在更接近哪一种想法？",
            quickReplies=(),
            isExtra=True,
        )
    return question(question_id)


def run_dialogue_scenario(scenario: DialogueScenario) -> DialogueRunResult:
    state = conversation().model_copy(
        update={"conversationId": f"conversation-{scenario.scenarioId}"}
    )
    asked_questions: list[str] = []
    stage_history: list[ConversationStage] = []
    conflicts_seen: list[str] = []

    for index, turn in enumerate(scenario.turns, start=1):
        turn_id = f"turn-{index}"
        message_id = f"message-{index}"
        expected_question = _expected_question(turn.expectedQuestionId)
        provider = provider_for_turn(
            state,
            message_text=turn.text,
            changes=turn.changes,
            next_question=expected_question,
            is_explicit_edit=turn.isExplicitEdit,
            scenario_id=scenario.scenarioId,
            turn_id=turn_id,
            message_id=message_id,
        )
        result = build_agent_graph(provider).invoke(
            graph_input(
                state,
                message_text=turn.text,
                candidate_impact=turn.candidateImpact,
                scenario_id=scenario.scenarioId,
                turn_id=turn_id,
                message_id=message_id,
                occurred_at=NOW + timedelta(minutes=index),
            )
        )
        state = result["conversation"]
        actual_question = result.get("nextQuestion")
        actual_question_id = (
            actual_question.questionId if actual_question is not None else None
        )
        if actual_question_id != turn.expectedQuestionId:
            raise AssertionError(
                f"{scenario.scenarioId} {turn_id}: expected "
                f"{turn.expectedQuestionId}, got {actual_question_id}"
            )
        if actual_question_id is not None:
            asked_questions.append(actual_question_id)
        stage_history.append(state.stage)
        for code in state.conflicts:
            if code not in conflicts_seen:
                conflicts_seen.append(code)

    if state.stage is not ConversationStage.READY_TO_MATCH:
        raise AssertionError(
            f"{scenario.scenarioId}: dialogue ended in {state.stage}, not READY_TO_MATCH"
        )
    match_result = build_agent_graph().invoke(
        {
            "conversation": state,
            "scenarioId": scenario.scenarioId,
            "turnId": "match",
            "trace": (),
        }
    )
    state = match_result["conversation"]
    stage_history.append(state.stage)
    return DialogueRunResult(
        scenarioId=scenario.scenarioId,
        turnCount=len(scenario.turns),
        askedQuestionIds=tuple(asked_questions),
        stageHistory=tuple(stage_history),
        conflictCodesSeen=tuple(conflicts_seen),
        finalState=state,
    )


def _confirmed_change(slot_name: ProfileSlotName, value: ProfileValue) -> ProfileChange:
    return ProfileChange(
        slotName=slot_name,
        value=value,
        status=SlotStatus.CONFIRMED,
    )


MULTI_TURN_SCENARIOS = (
    DialogueScenario(
        scenarioId="complete-recommendation",
        turns=(
            DialogueTurn(
                text="我想认识一只成年英国短毛猫，偏中等体型和短毛。",
                changes=(
                    _confirmed_change("speciesScope", ("CAT",)),
                    _confirmed_change(
                        "directionAndSizePreference", ("cat-british-shorthair",)
                    ),
                    _confirmed_change("agePreference", "ADULT"),
                    _confirmed_change("coatAppearancePreference", ("SHORT_HAIR",)),
                ),
                expectedQuestionId="ask-current-time",
            ),
            DialogueTurn(
                text="工作日能留出一些时间，希望活动量不用太高。",
                changes=(_confirmed_change("currentTimeArrangement", "LOW_MEDIUM"),),
                expectedQuestionId="ask-relationship-style",
            ),
            DialogueTurn(
                text="我喜欢安静一点的互动，待在附近陪着就很好。",
                changes=(
                    _confirmed_change("interactionRhythm", "LOW_MEDIUM"),
                    _confirmed_change("companionshipDistance", "NEARBY"),
                ),
                expectedQuestionId="ask-daily-burden",
            ),
            DialogueTurn(
                text="我能接受规律梳毛和中等花费，没有绝对不能接受的日常负担。",
                changes=(
                    _confirmed_change("ongoingInvestmentWillingness", "MEDIUM"),
                    _confirmed_change(
                        "disturbanceTolerance",
                        ("SHEDDING_MEDIUM_HIGH", "NOISE_LOW"),
                    ),
                    _confirmed_change("absoluteBottomLines", ()),
                ),
                expectedQuestionId="confirm-species-allergy",
            ),
            DialogueTurn(
                text="猫狗都不过敏。",
                changes=(_confirmed_change("allergySpecies", ()),),
                expectedQuestionId=None,
            ),
        ),
    ),
    DialogueScenario(
        scenarioId="conflict-clarification",
        turns=(
            DialogueTurn(
                text="我想养成年拉布拉多，喜欢互动积极的大型短毛狗。",
                changes=(
                    _confirmed_change("speciesScope", ("DOG",)),
                    _confirmed_change(
                        "directionAndSizePreference", ("dog-labrador-retriever",)
                    ),
                    _confirmed_change("agePreference", "ADULT"),
                    _confirmed_change("coatAppearancePreference", ("SHORT_HAIR",)),
                    _confirmed_change("interactionRhythm", "HIGH"),
                ),
                expectedQuestionId="ask-current-time",
            ),
            DialogueTurn(
                text="我每天能安排比较多的活动时间。",
                changes=(_confirmed_change("currentTimeArrangement", "HIGH"),),
                expectedQuestionId="ask-relationship-style",
            ),
            DialogueTurn(
                text="仔细想想，我其实更想要节奏中等、安静待在附近的陪伴。",
                changes=(
                    _confirmed_change("interactionRhythm", "MEDIUM"),
                    _confirmed_change("companionshipDistance", "NEARBY"),
                ),
                expectedQuestionId="clarify-slot-interactionRhythm",
            ),
            DialogueTurn(
                text="以现在的想法为准，我确定选择节奏中等。",
                changes=(_confirmed_change("interactionRhythm", "MEDIUM"),),
                expectedQuestionId="ask-daily-burden",
                isExplicitEdit=True,
            ),
            DialogueTurn(
                text="活动训练和长期投入我都能接受，也没有绝对底线。",
                changes=(
                    _confirmed_change("ongoingInvestmentWillingness", "HIGH"),
                    _confirmed_change(
                        "disturbanceTolerance", ("SHEDDING_HIGH", "NOISE_LOW")
                    ),
                    _confirmed_change("absoluteBottomLines", ()),
                ),
                expectedQuestionId="confirm-species-allergy",
            ),
            DialogueTurn(
                text="猫狗都不过敏。",
                changes=(_confirmed_change("allergySpecies", ()),),
                expectedQuestionId=None,
            ),
        ),
    ),
    DialogueScenario(
        scenarioId="allergy-not-recommended",
        turns=(
            DialogueTurn(
                text="我喜欢成年布偶猫，大体型、半长毛都可以。",
                changes=(
                    _confirmed_change("speciesScope", ("CAT",)),
                    _confirmed_change("directionAndSizePreference", ("cat-ragdoll",)),
                    _confirmed_change("agePreference", "ADULT"),
                    _confirmed_change("coatAppearancePreference", ("SEMI_LONG_HAIR",)),
                ),
                expectedQuestionId="ask-current-time",
            ),
            DialogueTurn(
                text="每天可以安排中等程度的陪伴和活动时间。",
                changes=(_confirmed_change("currentTimeArrangement", "MEDIUM"),),
                expectedQuestionId="ask-relationship-style",
            ),
            DialogueTurn(
                text="希望互动轻柔一些，也喜欢它待得近一点。",
                changes=(
                    _confirmed_change("interactionRhythm", "LOW_MEDIUM"),
                    _confirmed_change("companionshipDistance", "CLOSE"),
                ),
                expectedQuestionId="ask-daily-burden",
            ),
            DialogueTurn(
                text="梳毛和长期投入都能接受，没有其他绝对底线。",
                changes=(
                    _confirmed_change("ongoingInvestmentWillingness", "HIGH"),
                    _confirmed_change(
                        "disturbanceTolerance",
                        ("SHEDDING_MEDIUM_HIGH", "NOISE_LOW"),
                    ),
                    _confirmed_change("absoluteBottomLines", ()),
                ),
                expectedQuestionId="confirm-species-allergy",
            ),
            DialogueTurn(
                text="我已经确认自己对猫过敏。",
                changes=(_confirmed_change("allergySpecies", ("CAT",)),),
                expectedQuestionId=None,
            ),
        ),
    ),
)
