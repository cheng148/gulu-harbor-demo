from datetime import UTC, datetime

from app.domain.matching import (
    FACTOR_WEIGHTS,
    FactorAssessment,
    FitRatio,
    ScoringFactor,
    load_catalog,
    score_assessments,
    score_pet_candidate,
)
from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)

NOW = datetime(2026, 8, 9, tzinfo=UTC)


def confirmed[T](value: T) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=ConstraintStrength.PREFERENCE,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def assessments(default: FitRatio = FitRatio.FULL) -> tuple[FactorAssessment, ...]:
    return tuple(
        FactorAssessment(factor=factor, ratio=default, status=SlotStatus.CONFIRMED, reason="测试")
        for factor in ScoringFactor
    )


def test_approved_weights_total_one_hundred_and_keep_time_lowest() -> None:
    assert FACTOR_WEIGHTS == {
        ScoringFactor.DIRECTION_SIZE: 20,
        ScoringFactor.AGE: 10,
        ScoringFactor.COAT_APPEARANCE: 10,
        ScoringFactor.INTERACTION_RHYTHM: 20,
        ScoringFactor.COMPANIONSHIP_DISTANCE: 10,
        ScoringFactor.CURRENT_TIME: 5,
        ScoringFactor.ONGOING_INVESTMENT: 15,
        ScoringFactor.DISTURBANCE_TOLERANCE: 10,
    }
    assert sum(FACTOR_WEIGHTS.values()) == 100
    assert FACTOR_WEIGHTS[ScoringFactor.CURRENT_TIME] == min(FACTOR_WEIGHTS.values())


def test_each_factor_uses_only_the_four_approved_ratios() -> None:
    expected = {
        FitRatio.FULL: 100,
        FitRatio.ADJUSTED: 75,
        FitRatio.UNKNOWN: 50,
        FitRatio.MISMATCH: 0,
    }
    for ratio, total in expected.items():
        assert score_assessments(assessments(ratio)).total == total


def test_unknown_gets_half_weight_but_remains_unknown() -> None:
    items = list(assessments())
    items[0] = FactorAssessment(
        factor=ScoringFactor.DIRECTION_SIZE,
        ratio=FitRatio.UNKNOWN,
        status=SlotStatus.UNKNOWN,
        reason="用户尚未说明",
    )

    result = score_assessments(tuple(items))

    assert result.total == 90
    assert result.importantUnknowns == (ScoringFactor.DIRECTION_SIZE,)


def test_accepted_adjustment_changes_only_that_factor_to_seventy_five_percent() -> None:
    pet = load_catalog().pets[0]
    profile = PetPreferenceProfile(
        directionAndSizePreference=confirmed(("dog-labrador-retriever",)),
        agePreference=confirmed("ANY"),
        coatAppearancePreference=confirmed(("ANY",)),
        interactionRhythm=confirmed("ANY"),
        companionshipDistance=confirmed("ANY"),
        currentTimeArrangement=confirmed("ANY"),
        ongoingInvestmentWillingness=confirmed("ANY"),
        disturbanceTolerance=confirmed(("ANY",)),
        acceptedAdjustments=confirmed(("directionAndSizePreference",)),
    )

    result = score_pet_candidate(profile, pet)
    by_factor = {item.factor: item for item in result.assessments}

    assert result.total == 95
    assert by_factor[ScoringFactor.DIRECTION_SIZE].ratio is FitRatio.ADJUSTED
    assert all(
        item.ratio is FitRatio.FULL
        for factor, item in by_factor.items()
        if factor is not ScoringFactor.DIRECTION_SIZE
    )


def test_species_scope_filters_candidates_but_never_changes_score() -> None:
    pet = load_catalog().pets[0]
    base = PetPreferenceProfile()
    cat_scope = PetPreferenceProfile(speciesScope=confirmed(("CAT",)))

    assert score_pet_candidate(base, pet).total == score_pet_candidate(cat_scope, pet).total