from __future__ import annotations

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.nodes import (
    AgentGraphState,
    evaluate_profile,
    inspect_stage,
    make_ask_question,
    make_extract_profile,
    make_match_candidates,
    merge_profile_output,
    select_question,
    validate_profile_output,
)
from app.agent.routes import AgentRoute, route_from_stage
from app.domain.catalog import Catalog
from app.domain.matching import load_catalog
from app.providers.base import ModelProvider
from app.services.retrieval import KnowledgeRetriever, LocalKnowledgeRetriever


def _entry_route(state: AgentGraphState) -> AgentRoute:
    return route_from_stage(state["conversation"].stage)


def _question_route(state: AgentGraphState) -> AgentRoute:
    return AgentRoute.ASK_QUESTION if state.get("nextQuestion") else AgentRoute.END


def build_agent_graph(
    provider: ModelProvider | None = None,
    *,
    catalog: Catalog | None = None,
    knowledge_retriever: KnowledgeRetriever | None = None,
) -> CompiledStateGraph[AgentGraphState, None, AgentGraphState, AgentGraphState]:
    selected_catalog = catalog or load_catalog()
    selected_retriever = knowledge_retriever or LocalKnowledgeRetriever()
    builder = StateGraph(AgentGraphState)
    builder.add_node("inspect_stage", RunnableLambda(inspect_stage))
    builder.add_node("ask_question", RunnableLambda(make_ask_question(provider)))
    builder.add_node("extract_profile", RunnableLambda(make_extract_profile(provider)))
    builder.add_node("validate_profile_output", RunnableLambda(validate_profile_output))
    builder.add_node("merge_profile", RunnableLambda(merge_profile_output))
    builder.add_node("evaluate_profile", RunnableLambda(evaluate_profile))
    builder.add_node("select_question", RunnableLambda(select_question))
    builder.add_node(
        "match_candidates",
        RunnableLambda(make_match_candidates(selected_catalog, selected_retriever)),
    )

    builder.add_edge(START, "inspect_stage")
    builder.add_conditional_edges(
        "inspect_stage",
        _entry_route,
        {
            AgentRoute.ASK_QUESTION: "evaluate_profile",
            AgentRoute.EXTRACT_PROFILE: "extract_profile",
            AgentRoute.MATCH_CANDIDATES: "match_candidates",
            AgentRoute.END: END,
        },
    )
    builder.add_edge("extract_profile", "validate_profile_output")
    builder.add_edge("validate_profile_output", "merge_profile")
    builder.add_edge("merge_profile", "evaluate_profile")
    builder.add_edge("evaluate_profile", "select_question")
    builder.add_conditional_edges(
        "select_question",
        _question_route,
        {
            AgentRoute.ASK_QUESTION: "ask_question",
            AgentRoute.END: END,
        },
    )
    builder.add_edge("ask_question", END)
    builder.add_edge("match_candidates", END)
    return builder.compile(name="gulu-port-pet-selection")
