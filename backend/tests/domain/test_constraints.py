from datetime import UTC, datetime

from app.domain.constraints import (
    CandidateRequirements,
    ConstraintOutcome,
    evaluate_candidate_constraints,
    evaluate_session_constraints,
)
from app.domain.profile import (
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


def candidate(*, candidate_id: str = "pet-1", species: str = "DOG") -> CandidateRequirements:
    return CandidateRequirements(
        candidateId=candidate_id,
        species=species,
        minimumExerciseMinutes=90,
        minimumMonthlyCostCny=900,
        minimumCompanionHours=4,
        maximumAloneHours=4,
        sheddingLevel="HIGH",
    )


def test_unknown_housing_permission_is_not_a_required_clarification() -> None:
    assert evaluate_session_constraints(PetPreferenceProfile()) == ()


def test_volunteered_housing_ban_is_not_automatically_a_platform_blocker() -> None:
    profile = PetPreferenceProfile(petAllowed=confirmed(YesNoUncertain.NO, hard=True))

    assert evaluate_session_constraints(profile) == ()


def test_cat_allergy_excludes_cat_but_not_dog() -> None:
    profile = PetPreferenceProfile(
        allergySpecies=confirmed(("CAT",), hard=True),
    )

    cat_decisions = evaluate_candidate_constraints(
        profile, candidate(candidate_id="cat-1", species="CAT")
    )
    dog_decisions = evaluate_candidate_constraints(
        profile, candidate(candidate_id="dog-1", species="DOG")
    )

    assert [item.code for item in cat_decisions] == ["SPECIES_ALLERGY"]
    assert cat_decisions[0].outcome is ConstraintOutcome.EXCLUDE_CANDIDATE
    assert dog_decisions == ()


def test_time_and_activity_gaps_do_not_exclude_a_candidate() -> None:
    profile = PetPreferenceProfile(
        dailyExerciseMinutes=confirmed(20, hard=True),
        dailyCompanionHours=confirmed(1, hard=True),
        aloneHours=confirmed(10, hard=True),
    )

    assert evaluate_candidate_constraints(profile, candidate()) == ()


def test_budget_gap_does_not_exclude_a_candidate() -> None:
    profile = PetPreferenceProfile(monthlyBudgetCny=confirmed(400, hard=True))

    assert evaluate_candidate_constraints(profile, candidate()) == ()


def test_ordinary_shedding_preference_does_not_exclude_a_candidate() -> None:
    profile = PetPreferenceProfile(sheddingTolerance=confirmed("LOW"))

    assert evaluate_candidate_constraints(profile, candidate()) == ()


def test_explicit_shedding_bottom_line_excludes_before_scoring() -> None:
    profile = PetPreferenceProfile(
        absoluteBottomLines=confirmed(("SHEDDING_MAX:LOW",), hard=True),
    )

    decisions = evaluate_candidate_constraints(profile, candidate())

    assert [item.code for item in decisions] == ["ABSOLUTE_BOTTOM_LINE"]
    assert decisions[0].outcome is ConstraintOutcome.EXCLUDE_CANDIDATE
    assert decisions[0].affectedSlots == ("absoluteBottomLines",)
