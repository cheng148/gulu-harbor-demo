from datetime import UTC, datetime

from app.domain.constraints import (
    CandidateRequirements,
    ConstraintOutcome,
    evaluate_candidate_constraints,
    evaluate_session_constraints,
)
from app.domain.profile import (
    AllergyLevel,
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
    YesNoUncertain,
)

NOW = datetime(2026, 8, 4, tzinfo=UTC)


def confirmed[T](value: T, *, hard: bool = False) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=ConstraintStrength.HARD if hard else ConstraintStrength.UNSET,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def test_housing_ban_blocks_the_whole_session() -> None:
    profile = PetPreferenceProfile(petAllowed=confirmed(YesNoUncertain.NO, hard=True))

    decisions = evaluate_session_constraints(profile)

    assert decisions[0].outcome is ConstraintOutcome.NOT_RECOMMENDED
    assert decisions[0].code == "PET_NOT_ALLOWED"


def test_unknown_permission_requires_clarification_instead_of_rejection() -> None:
    decisions = evaluate_session_constraints(PetPreferenceProfile())

    assert any(
        item.outcome is ConstraintOutcome.CLARIFY and item.code == "PET_PERMISSION_UNKNOWN"
        for item in decisions
    )
    assert not any(item.outcome is ConstraintOutcome.NOT_RECOMMENDED for item in decisions)


def test_severe_allergy_blocks_final_recommendation() -> None:
    profile = PetPreferenceProfile(
        petAllowed=confirmed(YesNoUncertain.YES),
        allergyLevel=confirmed(AllergyLevel.SEVERE, hard=True),
    )

    decisions = evaluate_session_constraints(profile)

    assert any(item.code == "SEVERE_ALLERGY_UNASSESSED" for item in decisions)
    assert any(item.outcome is ConstraintOutcome.BLOCK_FINAL for item in decisions)


def test_exercise_mismatch_excludes_only_that_candidate() -> None:
    profile = PetPreferenceProfile(dailyExerciseMinutes=confirmed(20, hard=True))
    candidate = CandidateRequirements(
        candidateId="high-energy-dog",
        minimumExerciseMinutes=90,
        minimumMonthlyCostCny=500,
    )

    decisions = evaluate_candidate_constraints(profile, candidate)

    assert decisions[0].outcome is ConstraintOutcome.EXCLUDE_CANDIDATE
    assert decisions[0].code == "EXERCISE_INSUFFICIENT"


def test_hard_budget_excludes_candidate_before_soft_preferences() -> None:
    profile = PetPreferenceProfile(monthlyBudgetCny=confirmed(400, hard=True))
    candidate = CandidateRequirements(
        candidateId="expensive-perfect-looking-pet",
        minimumExerciseMinutes=10,
        minimumMonthlyCostCny=900,
    )

    decisions = evaluate_candidate_constraints(profile, candidate)

    assert any(
        item.outcome is ConstraintOutcome.EXCLUDE_CANDIDATE
        and item.code == "BUDGET_TOO_LOW"
        for item in decisions
    )
