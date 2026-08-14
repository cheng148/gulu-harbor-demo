from datetime import UTC, datetime

from app.domain.matching import load_catalog, match_direction_candidates
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue

NOW = datetime(2026, 8, 10, tzinfo=UTC)


def confirmed[ValueT](value: ValueT) -> SlotValue[ValueT]:
    return SlotValue[ValueT](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("seed",),
        updatedAt=NOW,
    )


def test_direction_matching_uses_direction_traits_without_pet_candidates() -> None:
    catalog = load_catalog()
    profile = PetPreferenceProfile(
        speciesScope=confirmed(("CAT",)),
        directionAndSizePreference=confirmed(("cat-british-shorthair",)),
        agePreference=confirmed("ADULT"),
        coatAppearancePreference=confirmed(("SHORT_HAIR",)),
        interactionRhythm=confirmed("LOW_MEDIUM"),
        companionshipDistance=confirmed("NEARBY"),
        currentTimeArrangement=confirmed("LOW_MEDIUM"),
        ongoingInvestmentWillingness=confirmed("MEDIUM"),
        disturbanceTolerance=confirmed(("SHEDDING_MEDIUM_HIGH", "NOISE_LOW")),
    )

    candidates = match_direction_candidates(profile, catalog.directions)

    assert candidates[0].targetId == "cat-british-shorthair"
    assert candidates[0].directionId == "cat-british-shorthair"


def test_direction_matching_filters_confirmed_species_allergy() -> None:
    catalog = load_catalog()
    profile = PetPreferenceProfile(
        speciesScope=confirmed(("CAT",)),
        allergySpecies=confirmed(("CAT",)),
    )

    assert match_direction_candidates(profile, catalog.directions) == ()
