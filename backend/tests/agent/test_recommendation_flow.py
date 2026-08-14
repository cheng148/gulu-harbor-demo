from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest

from app.agent.graph import build_agent_graph
from app.agent.nodes import AgentGraphState
from app.domain.catalog import Catalog, Species
from app.domain.errors import KnowledgeUnavailableError
from app.domain.knowledge import KnowledgeEntry
from app.domain.matching import load_catalog
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue
from app.domain.state import ConversationStage, ConversationState, RecommendationMode
from app.services.retrieval import (
    KnowledgeRetriever,
    load_knowledge,
    retrieve_knowledge,
)

NOW = datetime(2026, 8, 10, 12, tzinfo=UTC)


def confirmed[ValueT](value: ValueT) -> SlotValue[ValueT]:
    return SlotValue[ValueT](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("seed",),
        updatedAt=NOW,
    )


def profile(*, allergies: tuple[str, ...] = ()) -> PetPreferenceProfile:
    return PetPreferenceProfile(
        speciesScope=confirmed(("CAT",)),
        directionAndSizePreference=confirmed(("cat-british-shorthair",)),
        agePreference=confirmed("ADULT"),
        coatAppearancePreference=confirmed(("SHORT_HAIR",)),
        interactionRhythm=confirmed("LOW_MEDIUM"),
        companionshipDistance=confirmed("NEARBY"),
        currentTimeArrangement=confirmed("LOW_MEDIUM"),
        ongoingInvestmentWillingness=confirmed("MEDIUM"),
        disturbanceTolerance=confirmed(("SHEDDING_MEDIUM_HIGH", "NOISE_LOW")),
        allergySpecies=confirmed(allergies),
    )


def conversation(user_profile: PetPreferenceProfile) -> ConversationState:
    return ConversationState(
        conversationId="conversation-recommendation",
        stage=ConversationStage.READY_TO_MATCH,
        profile=user_profile,
        createdAt=NOW - timedelta(minutes=2),
        lastActiveAt=NOW - timedelta(minutes=1),
        expiresAt=NOW + timedelta(hours=24),
    )


def graph_input(state: ConversationState) -> AgentGraphState:
    return {
        "conversation": state,
        "scenarioId": "recommendation-flow",
        "turnId": "turn-4",
        "trace": (),
    }


@dataclass
class SequencedRetriever(KnowledgeRetriever):
    responses: tuple[tuple[KnowledgeEntry, ...], ...]
    expanded_calls: list[bool] = field(default_factory=list)

    def search(
        self,
        required_source_ids: tuple[str, ...],
        species: tuple[Species, ...],
        *,
        expanded: bool,
    ) -> tuple[KnowledgeEntry, ...]:
        del required_source_ids, species
        self.expanded_calls.append(expanded)
        index = min(len(self.expanded_calls) - 1, len(self.responses) - 1)
        return self.responses[index]


def test_ready_profile_returns_sourced_two_layer_recommendation() -> None:
    result = build_agent_graph().invoke(graph_input(conversation(profile())))
    updated = result["conversation"]
    recommendation = updated.recommendations

    assert updated.stage is ConversationStage.RECOMMENDED
    assert updated.recommendationMode is RecommendationMode.FINAL
    assert recommendation is not None
    assert 1 <= len(recommendation.directions) <= 4
    assert 1 <= len(recommendation.pets) <= 4
    assert len({pet.directionId for pet in recommendation.pets}) == len(
        recommendation.pets
    )
    assert all(direction.evidence for direction in recommendation.directions)
    assert all(pet.evidence for pet in recommendation.pets)
    assert "internalScore" not in recommendation.model_dump_json()


def test_direction_is_ranked_independently_and_can_remain_without_a_pet() -> None:
    catalog = load_catalog()
    direction_only_catalog = Catalog(
        directions=catalog.directions,
        merchants=catalog.merchants,
        pets=(),
    )

    result = build_agent_graph(catalog=direction_only_catalog).invoke(
        graph_input(conversation(profile()))
    )
    recommendation = result["conversation"].recommendations

    assert recommendation is not None
    assert recommendation.directions[0].directionId == "cat-british-shorthair"
    assert recommendation.pets == ()
    assert recommendation.petAvailabilityNote == "当前Demo档案暂无合适个体"


def test_knowledge_lookup_expands_once_before_succeeding() -> None:
    entries = load_knowledge()
    retriever = SequencedRetriever(responses=((), entries))
    required = ("tica-british-shorthair",)

    result = retrieve_knowledge(retriever, required, (Species.CAT,))

    assert {entry.sourceId for entry in result} >= set(required)
    assert retriever.expanded_calls == [False, True]


def test_missing_knowledge_after_expansion_aborts_without_mutating_state() -> None:
    retriever = SequencedRetriever(responses=((), ()))
    original = conversation(profile())
    snapshot = original.model_copy(deep=True)

    with pytest.raises(KnowledgeUnavailableError):
        build_agent_graph(knowledge_retriever=retriever).invoke(graph_input(original))

    assert retriever.expanded_calls == [False, True]
    assert original == snapshot


def test_allergic_species_returns_not_recommended_without_knowledge_lookup() -> None:
    retriever = SequencedRetriever(responses=((), ()))
    original = conversation(profile(allergies=("CAT",)))

    result = build_agent_graph(knowledge_retriever=retriever).invoke(
        graph_input(original)
    )
    updated = result["conversation"]

    assert updated.stage is ConversationStage.NOT_RECOMMENDED
    assert updated.recommendationMode is RecommendationMode.FINAL
    assert updated.recommendations is not None
    assert updated.recommendations.directions == ()
    assert updated.recommendations.pets == ()
    assert retriever.expanded_calls == []
