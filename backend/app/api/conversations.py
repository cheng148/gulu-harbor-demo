from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from fastapi import APIRouter, Request, Response

from app.agent.graph import build_agent_graph
from app.agent.nodes import (
    AgentGraphState,
    evaluate_profile,
    make_ask_question,
    select_question,
)
from app.api.errors import (
    PublicAPIError,
    PublicErrorResponse,
    ResponseMeta,
    get_request_id,
)
from app.api.schemas import (
    CreateConversationData,
    CreateConversationRequest,
    CreateConversationResponse,
    GetConversationData,
    GetConversationResponse,
    PatchProfileRequest,
    PublicConversationSummary,
    PublicMessage,
    PublicProfileChange,
    PublicProfileSlotName,
    PublicQuestion,
    PublicRecommendationChange,
    PublicSlotSummary,
    RecommendationData,
    RecommendationResponse,
    SendMessageRequest,
    TurnData,
    TurnResponse,
)
from app.core.clock import Clock
from app.domain.conflicts import detect_conflicts
from app.domain.constraints import evaluate_session_constraints
from app.domain.errors import (
    ConversationNotFoundError,
    KnowledgeUnavailableError,
    RevisionConflictError,
    SessionExpiredError,
)
from app.domain.matching import PublicRecommendation
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue
from app.domain.profile_merge import ProfileChange, ProfileDelta, merge_profile
from app.domain.questions import (
    NextQuestion,
    load_question_rules,
    select_next_question,
)
from app.domain.state import (
    ConversationStage,
    ConversationState,
    MessageRecord,
    MessageRole,
)
from app.providers.base import ModelProvider, ProviderFailure, ProviderFailureCode
from app.services.recommendation_narrative import add_safe_ai_narrative
from app.services.session_service import SessionService
from app.services.turn_service import TurnService

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

WELCOME_TEXT = "嗨，我是咕噜港的选宠搭子。我们从你的日常慢慢聊起，一起看看什么样的伙伴更适合你。"
RECOMMENDATION_TEXT = "我把目前聊到的情况整理好了，也找到了几位值得认识的伙伴。"
PUBLIC_PROFILE_SLOTS: tuple[PublicProfileSlotName, ...] = (
    "speciesScope", "directionAndSizePreference", "agePreference",
    "coatAppearancePreference", "interactionRhythm", "companionshipDistance",
    "currentTimeArrangement", "ongoingInvestmentWillingness",
    "disturbanceTolerance", "allergySpecies", "absoluteBottomLines",
    "acceptedAdjustments", "priorityNotes", "volunteeredContext",
)


def _app_service(request: Request, name: str, expected_type: type[Any]) -> Any:
    service = getattr(request.app.state, name, None)
    if not isinstance(service, expected_type):
        raise TypeError(f"{name} is not configured")
    return service


def _session_service(request: Request) -> SessionService:
    return cast(SessionService, _app_service(request, "session_service", SessionService))


def _turn_service(request: Request) -> TurnService:
    return cast(TurnService, _app_service(request, "turn_service", TurnService))


def _clock(request: Request) -> Clock:
    value = getattr(request.app.state, "clock", None)
    if value is None or not hasattr(value, "now"):
        raise TypeError("clock is not configured")
    return cast(Clock, value)


def _model_provider(request: Request) -> ModelProvider:
    provider = getattr(request.app.state, "model_provider", None)
    if provider is None or not isinstance(provider, ModelProvider):
        raise PublicAPIError(
            status_code=503,
            code="MODEL_UNAVAILABLE",
            message="选宠搭子暂时没有回应，请稍后再试。",
            retryable=True,
        )
    return provider


def _public_slot(slot: SlotValue[Any]) -> PublicSlotSummary:
    return PublicSlotSummary(value=slot.value, status=slot.status)


def _profile_summary(profile: PetPreferenceProfile) -> dict[str, PublicSlotSummary]:
    return {name: _public_slot(getattr(profile, name)) for name in PUBLIC_PROFILE_SLOTS}


def _public_conversation(state: ConversationState) -> PublicConversationSummary:
    return PublicConversationSummary(
        conversationId=state.conversationId,
        revision=state.revision,
        stage=state.stage,
        recommendationMode=state.recommendationMode,
        profileSummary=_profile_summary(state.profile),
        missingCriticalSlots=state.missingCriticalSlots,
        activeBlockers=state.activeBlockers,
        conflicts=state.conflicts,
        lastActiveAt=state.lastActiveAt,
        expiresAt=state.expiresAt,
    )


def _welcome_message(state: ConversationState) -> PublicMessage:
    return PublicMessage(
        messageId=f"msg_welcome_{state.conversationId}",
        role="ASSISTANT",
        content=WELCOME_TEXT,
        createdAt=state.createdAt,
    )


def _public_message(message: MessageRecord) -> PublicMessage:
    return PublicMessage(
        messageId=message.messageId,
        role="USER" if message.role is MessageRole.USER else "ASSISTANT",
        content=message.content,
        createdAt=message.createdAt,
    )


def _public_question(question: NextQuestion | None) -> PublicQuestion | None:
    if question is None:
        return None
    return PublicQuestion(
        questionId=question.questionId,
        text=question.prompt,
        quickReplies=question.quickReplies,
    )


def _current_question(state: ConversationState) -> PublicQuestion | None:
    if state.stage not in {
        ConversationStage.DISCOVERING,
        ConversationStage.RESOLVING_CONFLICT,
    }:
        return None
    if state.questionHistory and state.missingCriticalSlots:
        question_id = state.questionHistory[-1]
        rule = next(
            (item for item in load_question_rules() if item.questionId == question_id),
            None,
        )
        text = (
            state.messages[-1].content
            if state.messages and state.messages[-1].role is MessageRole.ASSISTANT
            else (rule.prompt if rule is not None else "这项情况现在更接近哪一种呢？")
        )
        return PublicQuestion(
            questionId=question_id,
            text=text,
            quickReplies=rule.quickReplies if rule is not None else (),
        )
    return _public_question(
        select_next_question(
            state.profile,
            evaluate_session_constraints(state.profile),
            detect_conflicts(state.profile),
            questionHistory=state.questionHistory,
            coreQuestionCount=state.coreQuestionCount,
            extraQuestionUsed=state.extraQuestionUsed,
        )
    )


def _public_messages(state: ConversationState) -> tuple[PublicMessage, ...]:
    return (_welcome_message(state), *tuple(_public_message(item) for item in state.messages))


def _raise_public_error(error: Exception, current_revision: int | None = None) -> None:
    if isinstance(error, SessionExpiredError):
        raise PublicAPIError(
            status_code=410, code="SESSION_EXPIRED",
            message="这段对话已保存满24小时，请重新开始。", retryable=False,
        ) from error
    if isinstance(error, ConversationNotFoundError):
        raise PublicAPIError(
            status_code=404, code="CONVERSATION_NOT_FOUND",
            message="没有找到这段选宠对话，请重新开始。", retryable=False,
        ) from error
    if isinstance(error, RevisionConflictError):
        raise PublicAPIError(
            status_code=409, code="REVISION_CONFLICT",
            message="这段对话已在其他操作中更新，请刷新后再试。", retryable=True,
            details={"currentRevision": current_revision},
        ) from error
    if isinstance(error, KnowledgeUnavailableError):
        raise PublicAPIError(
            status_code=503, code="KNOWLEDGE_UNAVAILABLE",
            message="选宠资料暂时无法读取，请稍后再试。", retryable=True,
        ) from error
    if isinstance(error, ProviderFailure):
        invalid = error.code is ProviderFailureCode.INVALID_OUTPUT
        raise PublicAPIError(
            status_code=502 if invalid else 503,
            code="MODEL_INVALID_RESPONSE" if invalid else "MODEL_UNAVAILABLE",
            message="选宠搭子暂时没有整理好回答，请稍后再试。",
            retryable=True,
        ) from error
    raise error


def _profile_changes(
    state: ConversationState,
    source_id: str,
    previous: ConversationState | None = None,
) -> tuple[PublicProfileChange, ...]:
    result: list[PublicProfileChange] = []
    for name in PUBLIC_PROFILE_SLOTS:
        slot = getattr(state.profile, name)
        if source_id not in slot.sourceMessageIds:
            continue
        previous_slot = getattr(previous.profile, name) if previous is not None else None
        result.append(
            PublicProfileChange(
                slotName=name,
                previousValue=previous_slot.value if previous_slot is not None else None,
                value=slot.value,
                status=slot.status,
            )
        )
    return tuple(result)


def _assistant_message(state: ConversationState) -> PublicMessage:
    assistant = next(
        (item for item in reversed(state.messages) if item.role is MessageRole.ASSISTANT),
        None,
    )
    if assistant is None:
        raise RuntimeError("successful turn must produce an assistant message")
    return _public_message(assistant)


def _turn_data(
    state: ConversationState,
    *,
    source_id: str,
    previous: ConversationState | None = None,
    recommendation_changes: tuple[PublicRecommendationChange, ...] = (),
) -> TurnData:
    question = _current_question(state)
    return TurnData(
        conversation=_public_conversation(state),
        assistantMessage=_assistant_message(state),
        profileChanges=_profile_changes(state, source_id, previous),
        nextQuestion=question,
        quickReplies=question.quickReplies if question is not None else (),
        recommendation=state.recommendations,
        warnings=state.safetyFlags,
        recommendationChanges=recommendation_changes,
    )


def _run_message_graph(
    state: ConversationState,
    *,
    provider: ModelProvider,
    content: str,
    message_id: str,
    occurred_at: Any,
) -> ConversationState:
    input_state: AgentGraphState = {
        "conversation": state,
        "scenarioId": "api-conversation",
        "turnId": f"turn-{state.revision + 1}",
        "messageId": message_id,
        "messageText": content,
        "occurredAt": occurred_at,
        "candidateImpact": {},
        "trace": (),
    }
    result = build_agent_graph(provider).invoke(input_state)
    updated = cast(ConversationState, result["conversation"])
    if updated.stage is ConversationStage.READY_TO_MATCH:
        match_input: AgentGraphState = {
            "conversation": updated,
            "scenarioId": "api-conversation",
            "turnId": f"turn-{state.revision + 1}:match",
            "trace": (),
        }
        updated = cast(
            ConversationState, build_agent_graph().invoke(match_input)["conversation"]
        )
        if updated.recommendations is None:
            raise RuntimeError("matching must produce a public recommendation")
        recommendation, safety_flags = add_safe_ai_narrative(
            updated.recommendations,
            provider,
            scenario_id="api-conversation",
            step_id=f"turn-{state.revision + 1}:recommendation",
        )
        updated = updated.model_copy(
            update={
                "recommendations": recommendation,
                "safetyFlags": tuple(
                    dict.fromkeys((*updated.safetyFlags, *safety_flags))
                ),
            }
        )
        message = MessageRecord(
            messageId=f"{message_id}:recommendation",
            role=MessageRole.ASSISTANT,
            content=RECOMMENDATION_TEXT,
            createdAt=occurred_at,
        )
        updated = updated.model_copy(update={"messages": (*updated.messages, message)})
    return updated


def _recommendation_changes(
    previous: PublicRecommendation | None,
    current: PublicRecommendation | None,
) -> tuple[PublicRecommendationChange, ...]:
    if current is None:
        return ()
    if previous is None:
        return (
            PublicRecommendationChange(
                changeType="STATUS_CHANGED", detail="已根据最新条件生成推荐。"
            ),
        )
    old_levels = {item.petId: item.matchLevel for item in previous.pets}
    new_levels = {item.petId: item.matchLevel for item in current.pets}
    changes: list[PublicRecommendationChange] = []
    for pet_id in sorted(new_levels.keys() - old_levels.keys()):
        changes.append(PublicRecommendationChange(
            changeType="ADDED", subjectId=pet_id, detail="这位伙伴进入了新的推荐结果。"
        ))
    for pet_id in sorted(old_levels.keys() - new_levels.keys()):
        changes.append(PublicRecommendationChange(
            changeType="REMOVED", subjectId=pet_id, detail="这位伙伴不再进入当前推荐。"
        ))
    for pet_id in sorted(old_levels.keys() & new_levels.keys()):
        if old_levels[pet_id] != new_levels[pet_id]:
            changes.append(PublicRecommendationChange(
                changeType="LEVEL_CHANGED", subjectId=pet_id,
                detail="这位伙伴的匹配等级发生了变化。"
            ))
    return tuple(changes) or (
        PublicRecommendationChange(
            changeType="UNCHANGED", detail="推荐成员没有变化，理由已按新条件更新。"
        ),
    )


@router.post("", response_model=CreateConversationResponse, status_code=201)
def create_conversation(request: Request, payload: CreateConversationRequest) -> CreateConversationResponse:
    del payload
    state = _session_service(request).create(f"conv_{uuid4().hex}")
    question = _current_question(state)
    if question is None:
        raise RuntimeError("new conversation must have an initial question")
    return CreateConversationResponse(
        data=CreateConversationData(
            conversation=_public_conversation(state),
            assistantMessage=_welcome_message(state), nextQuestion=question,
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )


@router.post("/{conversation_id}/messages", response_model=TurnResponse)
def send_message(
    conversation_id: str, payload: SendMessageRequest, request: Request
) -> TurnResponse:
    sessions = _session_service(request)
    try:
        current = sessions.get(conversation_id)
        stored = _turn_service(request).get_stored_result(
            conversation_id, payload.clientMessageId
        )
        if stored is not None:
            return TurnResponse(
                data=_turn_data(stored, source_id=payload.clientMessageId),
                meta=ResponseMeta(requestId=get_request_id(request)),
            )
        question = _current_question(current)
        if payload.quickReplyId is not None and (
            question is None or payload.quickReplyId not in question.quickReplies
        ):
            raise PublicAPIError(
                status_code=422, code="INVALID_QUICK_REPLY",
                message="这个快捷选项已经失效，请重新选择或直接输入。",
                retryable=False,
            )
        provider = _model_provider(request)
        result = _turn_service(request).process_message(
            conversation_id,
            client_message_id=payload.clientMessageId,
            base_revision=payload.baseRevision,
            mutate=lambda state: _run_message_graph(
                state, provider=provider, content=payload.content,
                message_id=payload.clientMessageId, occurred_at=_clock(request).now(),
            ),
        )
    except PublicAPIError:
        raise
    except (ConversationNotFoundError, SessionExpiredError, RevisionConflictError,
            KnowledgeUnavailableError, ProviderFailure) as error:
        latest = getattr(request.app.state, "session_service", sessions)
        revision = None
        try:
            revision = latest.get(conversation_id).revision
        except (ConversationNotFoundError, SessionExpiredError):
            pass
        _raise_public_error(error, revision)
        raise AssertionError("unreachable") from error
    return TurnResponse(
        data=_turn_data(
            result.state, source_id=payload.clientMessageId,
            previous=None if result.replayed else current,
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )


@router.patch("/{conversation_id}/profile", response_model=TurnResponse)
def patch_profile(
    conversation_id: str, payload: PatchProfileRequest, request: Request
) -> TurnResponse:
    sessions = _session_service(request)
    source_id = f"profile-edit-{uuid4().hex}"
    try:
        current = sessions.get(conversation_id)
        changes = tuple(
            ProfileChange(
                slotName=name,
                value=update.value,
                status=SlotStatus.CONFIRMED,
                constraintStrength=update.constraintStrength,
            )
            for name, update in payload.updates.items()
        )

        def mutate(state: ConversationState) -> ConversationState:
            merged = merge_profile(
                state.profile,
                ProfileDelta(sourceMessageId=source_id, changes=changes),
                _clock(request).now(),
                explicit_edit=True,
            ).profile
            occurred_at = _clock(request).now()
            prepared = state.model_copy(update={
                "profile": merged,
                "stage": ConversationStage.DISCOVERING,
                "recommendations": None,
                "retrievedSourceIds": (),
                "directionCandidates": (),
                "petCandidateIds": (),
            })
            graph_state: AgentGraphState = {
                "conversation": prepared,
                "scenarioId": "api-profile-edit",
                "turnId": f"profile-edit-{state.revision + 1}",
                "messageId": source_id,
                "occurredAt": occurred_at,
                "trace": (),
            }
            graph_state.update(evaluate_profile(graph_state))
            graph_state.update(select_question(graph_state))
            if graph_state.get("nextQuestion") is not None:
                ask_question = make_ask_question(_model_provider(request))
                graph_state.update(ask_question(graph_state))
                return graph_state["conversation"]

            updated = cast(
                ConversationState,
                build_agent_graph().invoke(graph_state)["conversation"],
            )
            if updated.recommendations is None:
                raise RuntimeError("matching must produce a public recommendation")
            recommendation, safety_flags = add_safe_ai_narrative(
                updated.recommendations,
                _model_provider(request),
                scenario_id="api-profile-edit",
                step_id=f"profile-edit-{state.revision + 1}:recommendation",
            )
            updated = updated.model_copy(
                update={
                    "recommendations": recommendation,
                    "safetyFlags": tuple(
                        dict.fromkeys((*updated.safetyFlags, *safety_flags))
                    ),
                }
            )
            assistant = MessageRecord(
                messageId=f"{source_id}:recommendation",
                role=MessageRole.ASSISTANT,
                content="我已经按你刚修改的条件重新整理了推荐。",
                createdAt=occurred_at,
            )
            return updated.model_copy(update={"messages": (*updated.messages, assistant)})

        updated = sessions.commit_success(
            conversation_id, base_revision=payload.baseRevision, mutate=mutate
        )
    except (ConversationNotFoundError, SessionExpiredError, RevisionConflictError,
            KnowledgeUnavailableError, ProviderFailure) as error:
        revision = current.revision if "current" in locals() else None
        _raise_public_error(error, revision)
        raise AssertionError("unreachable") from error
    rec_changes = _recommendation_changes(current.recommendations, updated.recommendations)
    return TurnResponse(
        data=_turn_data(
            updated, source_id=source_id, previous=current,
            recommendation_changes=rec_changes,
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )


@router.get("/{conversation_id}/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    conversation_id: str, request: Request
) -> RecommendationResponse:
    try:
        state = _session_service(request).get(conversation_id)
    except (ConversationNotFoundError, SessionExpiredError) as error:
        _raise_public_error(error)
        raise AssertionError("unreachable") from error
    if state.stage not in {ConversationStage.RECOMMENDED, ConversationStage.NOT_RECOMMENDED} or state.recommendations is None:
        raise PublicAPIError(
            status_code=409, code="RECOMMENDATION_NOT_READY",
            message="还需要再聊一点，暂时没有形成推荐。", retryable=False,
        )
    return RecommendationResponse(
        data=RecommendationData(
            conversation=_public_conversation(state), recommendation=state.recommendations
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )


@router.get("/{conversation_id}", response_model=GetConversationResponse)
def get_conversation(conversation_id: str, request: Request) -> GetConversationResponse:
    try:
        state = _session_service(request).get(conversation_id)
    except (ConversationNotFoundError, SessionExpiredError) as error:
        _raise_public_error(error)
        raise AssertionError("unreachable") from error
    return GetConversationResponse(
        data=GetConversationData(
            conversation=_public_conversation(state), messages=_public_messages(state),
            currentQuestion=_current_question(state), recommendation=state.recommendations,
        ),
        meta=ResponseMeta(requestId=get_request_id(request)),
    )


@router.delete(
    "/{conversation_id}",
    status_code=204,
    response_class=Response,
    responses={
        404: {
            "model": PublicErrorResponse,
            "description": "会话不存在或已经重置",
        },
        410: {
            "model": PublicErrorResponse,
            "description": "会话已经过期",
        },
    },
)
def reset_conversation(conversation_id: str, request: Request) -> Response:
    try:
        _session_service(request).reset(conversation_id)
    except (ConversationNotFoundError, SessionExpiredError) as error:
        _raise_public_error(error)
        raise AssertionError("unreachable") from error
    return Response(status_code=204)
