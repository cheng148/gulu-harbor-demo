from datetime import UTC, datetime

from app.domain.matching import (
    InternalCandidate,
    MatchLevel,
    determine_match_level,
    load_catalog,
    match_pet_candidates,
    rank_internal_candidates,
)
from app.domain.profile import (
    ConstraintStrength,
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
)

NOW = datetime(2026, 8, 9, tzinfo=UTC)


def confirmed[T](value: T, *, hard: bool = False) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        constraintStrength=ConstraintStrength.HARD if hard else ConstraintStrength.PREFERENCE,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def candidate(
    target_id: str,
    direction_id: str,
    score: float,
    *,
    unresolved: bool = False,
    pending: tuple[str, ...] = (),
    accepted: bool = False,
    excluded: bool = False,
) -> InternalCandidate:
    return InternalCandidate(
        targetId=target_id,
        directionId=direction_id,
        internalScore=score,
        unresolvedRelationshipOrLifeZero=unresolved,
        pendingItems=pending,
        hasAcceptedCondition=accepted,
        hardExcluded=excluded,
    )


def test_level_boundaries_are_eighty_and_sixty() -> None:
    assert determine_match_level(candidate("a", "d", 80)) is MatchLevel.HIGH
    assert determine_match_level(candidate("b", "d", 79.99)) is MatchLevel.MEDIUM
    assert determine_match_level(candidate("c", "d", 60)) is MatchLevel.MEDIUM
    assert determine_match_level(candidate("d", "d", 59.99)) is None


def test_relationship_or_life_zero_forces_caution_even_above_eighty() -> None:
    item = candidate("a", "d", 85, unresolved=True)
    assert determine_match_level(item) is MatchLevel.CAUTION


def test_unknown_or_accepted_condition_prevents_high_level() -> None:
    assert determine_match_level(candidate("a", "d", 90, pending=("互动节奏",))) is MatchLevel.MEDIUM
    assert determine_match_level(candidate("b", "d", 90, accepted=True)) is MatchLevel.MEDIUM


def test_hard_exclusion_never_enters_formal_results() -> None:
    assert determine_match_level(candidate("a", "d", 100, excluded=True)) is None


def test_ranking_is_level_first_then_score_then_stable_id() -> None:
    ranked = rank_internal_candidates(
        (
            candidate("caution-95", "d3", 95, unresolved=True),
            candidate("medium-60", "d2", 60),
            candidate("high-b", "d1", 82),
            candidate("high-a", "d4", 82),
            candidate("below", "d5", 59),
        )
    )
    assert [item.targetId for item in ranked] == [
        "high-a",
        "high-b",
        "medium-60",
        "caution-95",
    ]


def test_species_scope_filters_without_adding_score() -> None:
    catalog = load_catalog()
    profile = PetPreferenceProfile(speciesScope=confirmed(("CAT",)))

    candidates = match_pet_candidates(profile, catalog.pets)

    pet_ids = {pet.petId for pet in catalog.pets if pet.species.value == "CAT"}
    assert {item.targetId for item in candidates} <= pet_ids


def test_explicit_shedding_bottom_line_cannot_be_offset_by_preferences() -> None:
    catalog = load_catalog()
    profile = PetPreferenceProfile(
        absoluteBottomLines=confirmed(("SHEDDING_MAX:LOW",), hard=True),
        directionAndSizePreference=confirmed(("dog-pembroke-corgi",)),
    )

    candidates = match_pet_candidates(profile, catalog.pets)

    assert not any(item.directionId == "dog-pembroke-corgi" for item in candidates)


def test_repeated_matching_is_deterministic() -> None:
    catalog = load_catalog()
    profile = PetPreferenceProfile()
    assert match_pet_candidates(profile, catalog.pets) == match_pet_candidates(profile, catalog.pets)