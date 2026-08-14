from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.catalog import DEMO_DISCLOSURE
from app.domain.state import ConversationStage, RecommendationMode
from tests.fixtures.dialogues import (
    MULTI_TURN_SCENARIOS,
    DialogueRunResult,
    DialogueScenario,
    run_dialogue_scenario,
)

EXPECTED_PATH = Path(__file__).parent.parent / "fixtures" / "expected_results.json"


def _summary(result: DialogueRunResult) -> dict[str, object]:
    recommendation = result.finalState.recommendations
    assert recommendation is not None
    return {
        "turnCount": result.turnCount,
        "askedQuestionIds": list(result.askedQuestionIds),
        "stageHistory": [stage.value for stage in result.stageHistory],
        "conflictCodesSeen": list(result.conflictCodesSeen),
        "stage": result.finalState.stage.value,
        "recommendationMode": result.finalState.recommendationMode.value,
        "directionIds": [item.directionId for item in recommendation.directions],
        "petIds": [item.petId for item in recommendation.pets],
    }


@pytest.mark.parametrize(
    "scenario", MULTI_TURN_SCENARIOS, ids=lambda item: item.scenarioId
)
def test_five_turn_dialogue_matches_approved_expected_result(
    scenario: DialogueScenario,
) -> None:
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    result = run_dialogue_scenario(scenario)

    assert result.turnCount >= 5
    assert _summary(result) == expected[result.scenarioId]


@pytest.mark.parametrize(
    "scenario", MULTI_TURN_SCENARIOS, ids=lambda item: item.scenarioId
)
def test_dialogue_structure_is_identical_across_three_runs(
    scenario: DialogueScenario,
) -> None:
    summaries = [_summary(run_dialogue_scenario(scenario)) for _ in range(3)]

    assert summaries[0] == summaries[1] == summaries[2]


def test_complete_conflict_and_not_recommended_paths_use_real_business_results() -> (
    None
):
    results = {
        scenario.scenarioId: run_dialogue_scenario(scenario)
        for scenario in MULTI_TURN_SCENARIOS
    }

    complete = results["complete-recommendation"].finalState
    assert complete.stage is ConversationStage.RECOMMENDED
    assert complete.recommendationMode is RecommendationMode.FINAL
    assert complete.recommendations is not None
    assert complete.recommendations.directions
    assert complete.recommendations.pets
    assert all(
        pet.listingDisclosure == DEMO_DISCLOSURE
        for pet in complete.recommendations.pets
    )
    assert "internalScore" not in complete.recommendations.model_dump_json()

    conflict = results["conflict-clarification"]
    assert "SLOT_VALUE_CONFLICT:interactionRhythm" in conflict.conflictCodesSeen
    assert ConversationStage.RESOLVING_CONFLICT in conflict.stageHistory
    assert conflict.finalState.stage is ConversationStage.RECOMMENDED

    not_recommended = results["allergy-not-recommended"].finalState
    assert not_recommended.stage is ConversationStage.NOT_RECOMMENDED
    assert not_recommended.recommendationMode is RecommendationMode.FINAL
    assert not_recommended.recommendations is not None
    assert not_recommended.recommendations.directions == ()
    assert not_recommended.recommendations.pets == ()
