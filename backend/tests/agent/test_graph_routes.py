from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.agent.graph import build_agent_graph
from app.agent.routes import AgentRoute, route_from_stage
from app.domain.profile import SlotStatus
from app.domain.profile_merge import ProfileChange, ProfileDelta
from app.domain.state import ConversationStage, ConversationState
from app.providers.base import (
    ProfileExtractionResponse,
    ProviderFailure,
    ProviderFailureCode,
)

NOW = datetime(2026, 8, 9, 12, tzinfo=UTC)


def conversation(stage: ConversationStage) -> ConversationState:
    return ConversationState(
        conversationId="conversation-1",
        stage=stage,
        createdAt=NOW,
        lastActiveAt=NOW,
        expiresAt=NOW + timedelta(hours=24),
    )


def profile_output() -> ProfileExtractionResponse:
    return ProfileExtractionResponse(
        delta=ProfileDelta(
            sourceMessageId="message-1",
            changes=(
                ProfileChange(
                    slotName="dailyCompanionHours",
                    value=2.0,
                    status=SlotStatus.CONFIRMED,
                ),
            ),
        )
    )


@pytest.mark.parametrize(
    ("stage", "expected"),
    (
        (ConversationStage.NEW, AgentRoute.ASK_QUESTION),
        (ConversationStage.DISCOVERING, AgentRoute.EXTRACT_PROFILE),
        (ConversationStage.RESOLVING_CONFLICT, AgentRoute.EXTRACT_PROFILE),
        (ConversationStage.READY_TO_MATCH, AgentRoute.MATCH_CANDIDATES),
        (ConversationStage.MATCHING, AgentRoute.MATCH_CANDIDATES),
        (ConversationStage.RECOMMENDED, AgentRoute.EXTRACT_PROFILE),
        (ConversationStage.NOT_RECOMMENDED, AgentRoute.EXTRACT_PROFILE),
        (ConversationStage.COMPLETED, AgentRoute.END),
        (ConversationStage.EXPIRED, AgentRoute.END),
        (ConversationStage.RESET, AgentRoute.END),
    ),
)
def test_each_conversation_stage_has_one_explicit_entry_route(
    stage: ConversationStage, expected: AgentRoute
) -> None:
    assert route_from_stage(stage) is expected


def test_graph_exposes_nodes_and_edges_instead_of_hiding_a_single_agent_loop() -> None:
    graph = build_agent_graph()
    visible_nodes = set(graph.get_graph().nodes)

    assert {
        "inspect_stage",
        "ask_question",
        "extract_profile",
        "validate_profile_output",
        "match_candidates",
    }.issubset(visible_nodes)


def test_validation_node_accepts_structured_provider_output() -> None:
    output = profile_output()
    graph = build_agent_graph()

    result = graph.nodes["validate_profile_output"].invoke(
        {
            "expectedMessageId": "message-1",
            "rawProfileOutput": output.model_dump(mode="python"),
            "trace": (),
        }
    )

    assert result["trace"] == ("validate_profile_output",)
    assert result["validatedProfileOutput"] == output


def test_invalid_provider_output_stops_before_state_can_change() -> None:
    output = profile_output()
    graph = build_agent_graph()
    original = conversation(ConversationStage.DISCOVERING)
    invalid = output.model_dump(mode="python")
    invalid["unexpected"] = "must be rejected"

    with pytest.raises(ProviderFailure) as error:
        graph.invoke(
            {
                "conversation": original,
                "expectedMessageId": "message-1",
                "rawProfileOutput": invalid,
                "trace": (),
            }
        )

    assert error.value.code is ProviderFailureCode.INVALID_OUTPUT
    assert original.profile == conversation(ConversationStage.DISCOVERING).profile
