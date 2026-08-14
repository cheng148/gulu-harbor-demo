from datetime import UTC, datetime

from app.domain.profile import (
    PetPreferenceProfile,
    SlotStatus,
    SlotValue,
    YesNoUncertain,
)
from app.domain.readiness import ReadinessOutcome, assess_readiness

NOW = datetime(2026, 8, 9, tzinfo=UTC)


def confirmed[T](value: T) -> SlotValue[T]:
    return SlotValue[T](
        value=value,
        status=SlotStatus.CONFIRMED,
        sourceMessageIds=("m-1",),
        updatedAt=NOW,
    )


def allergy_confirmed_profile() -> PetPreferenceProfile:
    return PetPreferenceProfile(allergySpecies=confirmed(("NONE",)))


def core_answered_profile() -> PetPreferenceProfile:
    return PetPreferenceProfile(
        currentTimeArrangement=confirmed("WORKDAY_ALONE_6_HOURS"),
        interactionRhythm=confirmed("CALM"),
        companionshipDistance=confirmed("NEARBY"),
        ongoingInvestmentWillingness=confirmed("MEDIUM"),
        disturbanceTolerance=confirmed(("SHEDDING_MEDIUM", "NOISE_LOW")),
        absoluteBottomLines=confirmed(("NONE",)),
        allergySpecies=confirmed(("NONE",)),
    )


def test_three_core_questions_and_known_allergy_are_ready_for_final() -> None:
    result = assess_readiness(core_answered_profile(), coreQuestionCount=3)

    assert result.outcome is ReadinessOutcome.FINAL
    assert result.missingCriticalSlots == ()


def test_stable_recommendation_can_finish_before_three_questions() -> None:
    result = assess_readiness(
        allergy_confirmed_profile(),
        coreQuestionCount=1,
        recommendationStable=True,
    )

    assert result.outcome is ReadinessOutcome.FINAL


def test_unknown_allergy_must_be_confirmed_even_when_user_requests_results() -> None:
    result = assess_readiness(PetPreferenceProfile(), requestDirect=True)

    assert result.outcome is ReadinessOutcome.CONTINUE_QUESTIONING
    assert result.missingCriticalSlots == ("allergySpecies",)
    assert result.blockingCodes == ("ALLERGY_CONFIRMATION_REQUIRED",)


def test_known_species_allergy_does_not_block_the_other_species() -> None:
    profile = PetPreferenceProfile(allergySpecies=confirmed(("CAT",)))

    result = assess_readiness(profile, requestDirect=True)

    assert result.outcome is ReadinessOutcome.PROVISIONAL
    assert result.blockingCodes == ()


def test_housing_disclosure_is_not_a_readiness_gate() -> None:
    profile = allergy_confirmed_profile().model_copy(
        update={"petAllowed": confirmed(YesNoUncertain.NO)}
    )

    result = assess_readiness(profile, requestDirect=True)

    assert result.outcome is ReadinessOutcome.PROVISIONAL
    assert "petAllowed" not in result.missingCriticalSlots


def test_important_unknown_requests_the_extra_question_when_unused() -> None:
    result = assess_readiness(
        allergy_confirmed_profile(),
        coreQuestionCount=3,
        importantUnknowns=("directionAndSizePreference",),
    )

    assert result.outcome is ReadinessOutcome.CONTINUE_QUESTIONING
    assert result.missingCriticalSlots == ("directionAndSizePreference",)
    assert result.blockingCodes == ("EXTRA_QUESTION_REQUIRED",)


def test_remaining_important_unknown_is_provisional_after_extra_question() -> None:
    result = assess_readiness(
        allergy_confirmed_profile(),
        coreQuestionCount=3,
        extraQuestionUsed=True,
        importantUnknowns=("directionAndSizePreference",),
    )

    assert result.outcome is ReadinessOutcome.PROVISIONAL
    assert result.missingCriticalSlots == ("directionAndSizePreference",)


def test_direct_request_is_provisional_and_only_exposes_important_unknowns() -> None:
    result = assess_readiness(
        allergy_confirmed_profile(),
        requestDirect=True,
        importantUnknowns=("companionshipDistance",),
    )

    assert result.outcome is ReadinessOutcome.PROVISIONAL
    assert result.missingCriticalSlots == ("companionshipDistance",)


def test_without_direct_request_or_stability_core_questions_continue() -> None:
    result = assess_readiness(allergy_confirmed_profile(), coreQuestionCount=1)

    assert result.outcome is ReadinessOutcome.CONTINUE_QUESTIONING
    assert "currentTimeArrangement" in result.missingCriticalSlots


def test_no_eligible_candidates_is_not_recommended() -> None:
    result = assess_readiness(
        core_answered_profile(),
        coreQuestionCount=3,
        allCandidatesExcluded=True,
    )

    assert result.outcome is ReadinessOutcome.NOT_RECOMMENDED
    assert result.blockingCodes == ("NO_ELIGIBLE_CANDIDATES",)
