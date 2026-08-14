from __future__ import annotations

import operator
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from pydantic import ValidationError
from typing_extensions import TypedDict

from app.domain.catalog import Catalog
from app.domain.conflicts import DetectedConflict, detect_conflicts
from app.domain.constraints import ConstraintDecision, evaluate_session_constraints
from app.domain.knowledge import KnowledgeEntry
from app.domain.matching import (
    build_public_recommendation,
    match_direction_candidates,
    match_pet_candidates,
)
from app.domain.profile import ConstraintStrength
from app.domain.profile_merge import ProfileDelta, merge_profile
from app.domain.questions import (
    NextQuestion,
    QuestionCategory,
    QuestionImpact,
    select_next_question,
)
from app.domain.state import (
    ConversationStage,
    ConversationState,
    MessageRecord,
    MessageRole,
    RecommendationMode,
)
from app.providers.base import (
    ModelProvider,
    ProfileExtractionRequest,
    ProfileExtractionResponse,
    ProviderFailure,
    ProviderFailureCode,
    QuestionWordingRequest,
    QuestionWordingResponse,
)
from app.services.retrieval import KnowledgeRetriever, retrieve_knowledge


class AgentGraphState(TypedDict, total=False):
    conversation: ConversationState
    scenarioId: str
    turnId: str
    messageId: str
    messageText: str
    occurredAt: datetime
    candidateImpact: dict[str, QuestionImpact]
    expectedMessageId: str
    rawProfileOutput: object
    validatedProfileOutput: ProfileExtractionResponse
    blockers: tuple[ConstraintDecision, ...]
    detectedConflicts: tuple[DetectedConflict, ...]
    nextQuestion: NextQuestion | None
    phrasedQuestion: QuestionWordingResponse
    trace: Annotated[tuple[str, ...], operator.add]


def inspect_stage(_: AgentGraphState) -> AgentGraphState:
    return {"trace": ("inspect_stage",)}


def make_ask_question(
    provider: ModelProvider | None,
) -> Callable[[AgentGraphState], AgentGraphState]:
    def ask_question(state: AgentGraphState) -> AgentGraphState:
        selected = state.get("nextQuestion")
        if selected is None:
            return {"trace": ("ask_question",)}
        if provider is None:
            raise ProviderFailure(
                ProviderFailureCode.UNAVAILABLE,
                "question wording requires a model provider",
            )

        request = QuestionWordingRequest(
            scenarioId=state["scenarioId"],
            stepId=f"{state['turnId']}:question",
            questionId=selected.questionId,
            prompt=selected.prompt,
            quickReplies=selected.quickReplies,
        )
        response = QuestionWordingResponse.model_validate(
            provider.phrase_question(request).model_dump(mode="python")
        )
        if (
            response.questionId != selected.questionId
            or response.quickReplies != selected.quickReplies
        ):
            raise ProviderFailure(
                ProviderFailureCode.INVALID_OUTPUT,
                "provider changed a question selected by deterministic rules",
            )

        conversation = state["conversation"]
        assistant_message = MessageRecord(
            messageId=f"{state['messageId']}:question",
            role=MessageRole.ASSISTANT,
            content=response.text,
            createdAt=state["occurredAt"],
        )
        return {
            "conversation": conversation.model_copy(
                update={"messages": (*conversation.messages, assistant_message)}
            ),
            "phrasedQuestion": response,
            "trace": ("ask_question",),
        }

    return ask_question


def make_extract_profile(
    provider: ModelProvider | None,
) -> Callable[[AgentGraphState], AgentGraphState]:
    def extract_profile(state: AgentGraphState) -> AgentGraphState:
        message_id = state.get("messageId", state.get("expectedMessageId", ""))
        if provider is None:
            return {
                "expectedMessageId": message_id,
                "trace": ("extract_profile",),
            }

        conversation = state["conversation"]
        request = ProfileExtractionRequest(
            scenarioId=state["scenarioId"],
            stepId=f"{state['turnId']}:extract",
            messageId=message_id,
            text=state["messageText"],
            currentQuestionId=(
                conversation.questionHistory[-1]
                if conversation.questionHistory
                else None
            ),
            currentProfile=conversation.profile,
        )
        response = provider.extract_profile(request)
        return {
            "expectedMessageId": message_id,
            "rawProfileOutput": response.model_dump(mode="python"),
            "trace": ("extract_profile",),
        }

    return extract_profile


def make_match_candidates(
    catalog: Catalog,
    knowledge_retriever: KnowledgeRetriever,
) -> Callable[[AgentGraphState], AgentGraphState]:
    def match_candidates(state: AgentGraphState) -> AgentGraphState:
        conversation = state["conversation"]
        direction_candidates = match_direction_candidates(
            conversation.profile,
            catalog.directions,
        )
        pet_candidates = match_pet_candidates(conversation.profile, catalog.pets)
        preliminary = build_public_recommendation(
            catalog,
            direction_candidates,
            pet_candidates,
        )

        knowledge_entries: tuple[KnowledgeEntry, ...] = ()
        if preliminary.directions:
            required_ids: list[str] = []
            for direction in preliminary.directions:
                required_ids.extend(direction.sourceIds)
            for pet in preliminary.pets:
                required_ids.extend(pet.sourceIds)
            required_source_ids = tuple(dict.fromkeys(required_ids))
            direction_map = {item.directionId: item for item in catalog.directions}
            species = tuple(
                dict.fromkeys(
                    direction_map[item.directionId].species
                    for item in preliminary.directions
                )
            )
            knowledge_entries = retrieve_knowledge(
                knowledge_retriever,
                required_source_ids,
                species,
            )

        recommendation = build_public_recommendation(
            catalog,
            direction_candidates,
            pet_candidates,
            knowledge_entries,
        )
        pending_values: list[str] = []
        for direction in recommendation.directions:
            pending_values.extend(direction.pendingItems)
        for pet in recommendation.pets:
            pending_values.extend(pet.pendingItems)
        pending_items = tuple(dict.fromkeys(pending_values))
        has_direction = bool(recommendation.directions)
        return {
            "conversation": conversation.model_copy(
                update={
                    "stage": (
                        ConversationStage.RECOMMENDED
                        if has_direction
                        else ConversationStage.NOT_RECOMMENDED
                    ),
                    "recommendationMode": (
                        RecommendationMode.PROVISIONAL
                        if pending_items
                        else RecommendationMode.FINAL
                    ),
                    "importantUnknowns": pending_items,
                    "retrievedSourceIds": tuple(
                        item.sourceId for item in knowledge_entries
                    ),
                    "directionCandidates": tuple(
                        item.directionId for item in recommendation.directions
                    ),
                    "petCandidateIds": tuple(
                        item.petId for item in recommendation.pets
                    ),
                    "recommendations": recommendation,
                }
            ),
            "trace": ("match_candidates",),
        }

    return match_candidates


def validate_profile_output(state: AgentGraphState) -> AgentGraphState:
    try:
        response = ProfileExtractionResponse.model_validate(state["rawProfileOutput"])
    except (KeyError, ValidationError) as error:
        raise ProviderFailure(
            ProviderFailureCode.INVALID_OUTPUT,
            "provider profile output failed schema validation",
        ) from error

    if response.delta.sourceMessageId != state.get("expectedMessageId"):
        raise ProviderFailure(
            ProviderFailureCode.INVALID_OUTPUT,
            "provider profile output belongs to a different message",
        )

    return {
        "validatedProfileOutput": response,
        "trace": ("validate_profile_output",),
    }


def _normalize_model_delta(delta: ProfileDelta) -> ProfileDelta:
    changes = tuple(
        change.model_copy(update={"constraintStrength": ConstraintStrength.PREFERENCE})
        if change.constraintStrength is ConstraintStrength.HARD
        and change.slotName not in {"allergySpecies", "absoluteBottomLines"}
        else change
        for change in delta.changes
    )
    return ProfileDelta(sourceMessageId=delta.sourceMessageId, changes=changes)


def merge_profile_output(state: AgentGraphState) -> AgentGraphState:
    conversation = state["conversation"]
    response = state["validatedProfileOutput"]
    occurred_at = state.get("occurredAt", conversation.lastActiveAt)
    result = merge_profile(
        conversation.profile,
        _normalize_model_delta(response.delta),
        occurred_at,
        explicit_edit=response.isExplicitEdit,
    )
    messages = conversation.messages
    if state.get("messageText") and state.get("messageId"):
        messages = (
            *messages,
            MessageRecord(
                messageId=state["messageId"],
                role=MessageRole.USER,
                content=state["messageText"],
                createdAt=occurred_at,
            ),
        )
    return {
        "conversation": conversation.model_copy(
            update={
                "profile": result.profile,
                "messages": messages,
                "retrievedSourceIds": (),
                "directionCandidates": (),
                "petCandidateIds": (),
                "recommendations": None,
                "safetyFlags": (),
            }
        ),
        "trace": ("merge_profile",),
    }


def evaluate_profile(state: AgentGraphState) -> AgentGraphState:
    conversation = state["conversation"]
    blockers = evaluate_session_constraints(conversation.profile)
    conflicts = detect_conflicts(conversation.profile)
    return {
        "conversation": conversation.model_copy(
            update={
                "activeBlockers": tuple(item.code for item in blockers),
                "conflicts": tuple(item.code for item in conflicts),
            }
        ),
        "blockers": blockers,
        "detectedConflicts": conflicts,
        "trace": ("evaluate_profile",),
    }


def select_question(state: AgentGraphState) -> AgentGraphState:
    conversation = state["conversation"]
    selected = select_next_question(
        conversation.profile,
        state.get("blockers", ()),
        state.get("detectedConflicts", ()),
        questionHistory=conversation.questionHistory,
        coreQuestionCount=conversation.coreQuestionCount,
        extraQuestionUsed=conversation.extraQuestionUsed,
        candidateImpact=state.get("candidateImpact", {}),
    )
    if selected is None:
        return {
            "conversation": conversation.model_copy(
                update={
                    "stage": ConversationStage.READY_TO_MATCH,
                    "missingCriticalSlots": (),
                }
            ),
            "nextQuestion": None,
            "trace": ("select_question",),
        }

    history = conversation.questionHistory
    is_new = selected.questionId not in history
    if is_new:
        history = (*history, selected.questionId)
    core_count = conversation.coreQuestionCount
    if is_new and selected.category is QuestionCategory.CORE:
        core_count += 1
    stage = (
        ConversationStage.RESOLVING_CONFLICT
        if selected.category is QuestionCategory.CONFLICT
        else ConversationStage.DISCOVERING
    )
    return {
        "conversation": conversation.model_copy(
            update={
                "stage": stage,
                "missingCriticalSlots": selected.targetSlots,
                "questionHistory": history,
                "coreQuestionCount": core_count,
                "extraQuestionUsed": (
                    conversation.extraQuestionUsed or selected.isExtra
                ),
            }
        ),
        "nextQuestion": selected,
        "trace": ("select_question",),
    }
