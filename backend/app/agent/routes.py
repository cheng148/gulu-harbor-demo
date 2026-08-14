from __future__ import annotations

from enum import StrEnum

from app.domain.state import ConversationStage


class AgentRoute(StrEnum):
    ASK_QUESTION = "ASK_QUESTION"
    EXTRACT_PROFILE = "EXTRACT_PROFILE"
    MATCH_CANDIDATES = "MATCH_CANDIDATES"
    END = "END"


_STAGE_ROUTES = {
    ConversationStage.NEW: AgentRoute.ASK_QUESTION,
    ConversationStage.DISCOVERING: AgentRoute.EXTRACT_PROFILE,
    ConversationStage.RESOLVING_CONFLICT: AgentRoute.EXTRACT_PROFILE,
    ConversationStage.READY_TO_MATCH: AgentRoute.MATCH_CANDIDATES,
    ConversationStage.MATCHING: AgentRoute.MATCH_CANDIDATES,
    ConversationStage.RECOMMENDED: AgentRoute.EXTRACT_PROFILE,
    ConversationStage.NOT_RECOMMENDED: AgentRoute.EXTRACT_PROFILE,
    ConversationStage.COMPLETED: AgentRoute.END,
    ConversationStage.EXPIRED: AgentRoute.END,
    ConversationStage.RESET: AgentRoute.END,
}


def route_from_stage(stage: ConversationStage) -> AgentRoute:
    return _STAGE_ROUTES[stage]
