from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.domain.profile import PetPreferenceProfile, SlotStatus


class ConstraintOutcome(StrEnum):
    NOT_RECOMMENDED = "NOT_RECOMMENDED"
    BLOCK_FINAL = "BLOCK_FINAL"
    EXCLUDE_CANDIDATE = "EXCLUDE_CANDIDATE"
    CLARIFY = "CLARIFY"


class ConstraintDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: ConstraintOutcome
    code: str
    reason: str
    affectedSlots: tuple[str, ...]


class CandidateRequirements(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidateId: str
    species: str = "DOG"
    minimumExerciseMinutes: int = Field(ge=0)
    minimumMonthlyCostCny: int = Field(ge=0)
    minimumCompanionHours: float = Field(default=0, ge=0, le=24)
    maximumAloneHours: float = Field(default=24, ge=0, le=24)
    size: str = "MEDIUM"
    sheddingLevel: str = "MEDIUM"
    noiseLevel: str = "MEDIUM"
    odorLevel: str = "MEDIUM"
    groomingLevel: str = "MEDIUM"
    unsuitableTags: tuple[str, ...] = ()
    listingType: str = "ADOPTION"


def evaluate_session_constraints(
    profile: PetPreferenceProfile,
) -> tuple[ConstraintDecision, ...]:
    del profile
    # Housing, household, budget, and care context are not mandatory gates in
    # the revised product. Species allergy and explicit bottom lines are
    # evaluated against each candidate, where their actual impact is known.
    return ()


_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _violates_bottom_line(line: str, candidate: CandidateRequirements) -> bool:
    key, separator, value = line.partition(":")
    if not separator or not value:
        return False

    maximum_levels = {
        "SHEDDING_MAX": candidate.sheddingLevel,
        "NOISE_MAX": candidate.noiseLevel,
        "ODOR_MAX": candidate.odorLevel,
        "GROOMING_MAX": candidate.groomingLevel,
    }
    if key in maximum_levels:
        candidate_level = maximum_levels[key]
        return (
            value in _LEVEL_RANK
            and candidate_level in _LEVEL_RANK
            and _LEVEL_RANK[candidate_level] > _LEVEL_RANK[value]
        )
    if key == "SIZE_NOT":
        return candidate.size == value
    if key == "SOURCE_ONLY":
        return candidate.listingType != value
    if key == "UNSUITABLE_TAG":
        return value in candidate.unsuitableTags
    return False


def evaluate_candidate_constraints(
    profile: PetPreferenceProfile,
    candidate: CandidateRequirements,
) -> tuple[ConstraintDecision, ...]:
    decisions: list[ConstraintDecision] = []

    allergy = profile.allergySpecies
    if (
        allergy.status is SlotStatus.CONFIRMED
        and allergy.value is not None
        and candidate.species in allergy.value
    ):
        decisions.append(
            ConstraintDecision(
                outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                code="SPECIES_ALLERGY",
                reason=f"用户已确认对{candidate.species}物种过敏。",
                affectedSlots=("allergySpecies",),
            )
        )

    bottom_lines = profile.absoluteBottomLines
    if bottom_lines.status is SlotStatus.CONFIRMED and bottom_lines.value is not None:
        for line in bottom_lines.value:
            if _violates_bottom_line(line, candidate):
                decisions.append(
                    ConstraintDecision(
                        outcome=ConstraintOutcome.EXCLUDE_CANDIDATE,
                        code="ABSOLUTE_BOTTOM_LINE",
                        reason="候选违反用户明确说出的绝对底线。",
                        affectedSlots=("absoluteBottomLines",),
                    )
                )

    return tuple(decisions)
