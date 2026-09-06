from __future__ import annotations

from datetime import UTC, datetime

from app.domain.constraints import (
    CandidateRequirements,
    ConstraintOutcome,
    evaluate_candidate_constraints,
)
from app.domain.matching import (
    FACTOR_WEIGHTS,
    InternalCandidate,
    ScoringFactor,
    build_public_recommendation,
    load_catalog,
    score_pet_candidate,
)
from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)

NOW = datetime(2026, 9, 6, tzinfo=UTC)


def confirmed[ValueT](value: ValueT, *, hard: bool = False) -> SlotValue[ValueT]:
    return SlotValue[ValueT](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=(
            ConstraintStrength.HARD if hard else ConstraintStrength.PREFERENCE
        ),
        sourceMessageIds=("eval",),
        updatedAt=NOW,
    )


def candidate(target_id: str, direction_id: str) -> InternalCandidate:
    return InternalCandidate(
        targetId=target_id,
        directionId=direction_id,
        internalScore=85,
        suitableReasons=("相处方式接近",),
        tradeoffs=("仍需线下继续了解",),
    )


def test_dog_allergy_excludes_dog_but_not_cat() -> None:
    profile = PetPreferenceProfile(
        allergySpecies=confirmed(("DOG",), hard=True),
    )
    dog = CandidateRequirements(
        candidateId="dog",
        species="DOG",
        minimumExerciseMinutes=0,
        minimumMonthlyCostCny=0,
    )
    cat = dog.model_copy(update={"candidateId": "cat", "species": "CAT"})

    dog_decisions = evaluate_candidate_constraints(profile, dog)

    assert [item.code for item in dog_decisions] == ["SPECIES_ALLERGY"]
    assert dog_decisions[0].outcome is ConstraintOutcome.EXCLUDE_CANDIDATE
    assert evaluate_candidate_constraints(profile, cat) == ()


def test_explicit_noise_bottom_line_excludes_before_scoring() -> None:
    profile = PetPreferenceProfile(
        absoluteBottomLines=confirmed(("NOISE_MAX:LOW",), hard=True),
    )
    noisy_pet = CandidateRequirements(
        candidateId="noisy",
        minimumExerciseMinutes=0,
        minimumMonthlyCostCny=0,
        noiseLevel="HIGH",
    )

    decisions = evaluate_candidate_constraints(profile, noisy_pet)

    assert [item.code for item in decisions] == ["ABSOLUTE_BOTTOM_LINE"]
    assert decisions[0].outcome is ConstraintOutcome.EXCLUDE_CANDIDATE


def test_wording_intensity_does_not_create_an_extra_scoring_factor() -> None:
    pet = load_catalog().pets[0]
    ordinary_wording_profile = PetPreferenceProfile(
        directionAndSizePreference=confirmed((pet.directionId,)),
    )
    strong_wording_same_meaning_profile = PetPreferenceProfile(
        directionAndSizePreference=confirmed((pet.directionId,)),
    )

    assert "WORDING_INTENSITY" not in {factor.value for factor in ScoringFactor}
    assert score_pet_candidate(
        ordinary_wording_profile, pet
    ) == score_pet_candidate(strong_wording_same_meaning_profile, pet)


def test_direction_and_size_share_one_scoring_factor() -> None:
    assert ScoringFactor.DIRECTION_SIZE in FACTOR_WEIGHTS
    assert not any(
        factor.value in {"DIRECTION", "SIZE"} for factor in FACTOR_WEIGHTS
    )
    assert len(FACTOR_WEIGHTS) == len(ScoringFactor) == 8


def test_two_eligible_pets_are_not_padded_to_four() -> None:
    catalog = load_catalog()
    directions = (
        candidate("cat-adult-local-mix", "cat-adult-local-mix"),
        candidate("cat-british-shorthair", "cat-british-shorthair"),
    )
    pets = (
        candidate("pet-cat-local-01", "cat-adult-local-mix"),
        candidate("pet-cat-british-01", "cat-british-shorthair"),
    )

    result = build_public_recommendation(catalog, directions, pets)

    assert len(result.directions) == 2
    assert len(result.pets) == 2
    assert {item.petId for item in result.pets} == {
        "pet-cat-local-01",
        "pet-cat-british-01",
    }
