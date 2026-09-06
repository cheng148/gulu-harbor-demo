from __future__ import annotations

import json
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.domain.catalog import (
    Catalog,
    CostLevel,
    DataNature,
    DirectionKind,
    DirectionProfile,
    ListingStatus,
    MerchantProfile,
    PetProfile,
)
from app.domain.knowledge import KnowledgeEntry
from app.domain.profile import PetPreferenceProfile, SlotStatus, SlotValue


class MatchLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    CAUTION = "CAUTION"


class ScoringFactor(StrEnum):
    DIRECTION_SIZE = "DIRECTION_SIZE"
    AGE = "AGE"
    COAT_APPEARANCE = "COAT_APPEARANCE"
    INTERACTION_RHYTHM = "INTERACTION_RHYTHM"
    COMPANIONSHIP_DISTANCE = "COMPANIONSHIP_DISTANCE"
    CURRENT_TIME = "CURRENT_TIME"
    ONGOING_INVESTMENT = "ONGOING_INVESTMENT"
    DISTURBANCE_TOLERANCE = "DISTURBANCE_TOLERANCE"


class FitRatio(float, Enum):
    FULL = 1.0
    ADJUSTED = 0.75
    UNKNOWN = 0.5
    MISMATCH = 0.0


FACTOR_WEIGHTS: dict[ScoringFactor, int] = {
    ScoringFactor.DIRECTION_SIZE: 20,
    ScoringFactor.AGE: 10,
    ScoringFactor.COAT_APPEARANCE: 10,
    ScoringFactor.INTERACTION_RHYTHM: 20,
    ScoringFactor.COMPANIONSHIP_DISTANCE: 10,
    ScoringFactor.CURRENT_TIME: 5,
    ScoringFactor.ONGOING_INVESTMENT: 15,
    ScoringFactor.DISTURBANCE_TOLERANCE: 10,
}

RELATION_OR_LIFE_FACTORS = {
    ScoringFactor.INTERACTION_RHYTHM,
    ScoringFactor.COMPANIONSHIP_DISTANCE,
    ScoringFactor.CURRENT_TIME,
    ScoringFactor.ONGOING_INVESTMENT,
    ScoringFactor.DISTURBANCE_TOLERANCE,
}
_NEUTRAL_VALUES = {"ANY", "ALL", "都可以", "没有要求", "NO_PREFERENCE"}
_LEVEL_ORDER = {"LOW": 0, "LOW_MEDIUM": 1, "MEDIUM": 2, "MEDIUM_HIGH": 3, "HIGH": 4}


class FactorAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    factor: ScoringFactor
    ratio: FitRatio
    status: SlotStatus
    reason: str = Field(min_length=1)


class CandidateScore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    total: float = Field(ge=0, le=100)
    assessments: tuple[FactorAssessment, ...]
    importantUnknowns: tuple[ScoringFactor, ...]
    unresolvedRelationshipOrLifeZero: bool
    hasAcceptedCondition: bool


class InternalCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    targetId: str
    directionId: str
    internalScore: float = Field(ge=0, le=100)
    mismatchPoints: tuple[str, ...] = ()
    suitableReasons: tuple[str, ...] = ()
    tradeoffs: tuple[str, ...] = ()
    pendingItems: tuple[str, ...] = ()
    unresolvedRelationshipOrLifeZero: bool = False
    hasAcceptedCondition: bool = False
    hasSmallDifference: bool = False
    fullyInformed: bool = True
    hardExcluded: bool = False

    @property
    def matchLevel(self) -> MatchLevel | None:
        return determine_match_level(self)


class PublicMerchantResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    merchantId: str
    displayName: str
    isSimulated: bool = True


class PublicEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sourceId: str
    sourceName: str
    sourceLocator: str


class PublicContactAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str = "DEMO_CONTACT_MERCHANT"
    label: str = "联系商家进一步了解"
    available: bool = False
    unavailableMessage: str = "Demo演示功能，暂未开放。"


class PublicDirectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    directionId: str
    name: str
    kind: DirectionKind
    matchLevel: MatchLevel
    suitableReasons: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    mismatchPoints: tuple[str, ...]
    pendingItems: tuple[str, ...]
    acquisitionCostLevel: CostLevel
    ongoingCareCostLevel: CostLevel
    sourceIds: tuple[str, ...]
    evidence: tuple[PublicEvidence, ...] = ()
    evidenceNote: str


class PublicPetResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    petId: str
    nickname: str
    directionId: str
    matchLevel: MatchLevel
    suitableReasons: tuple[str, ...]
    tradeoffs: tuple[str, ...]
    mismatchPoints: tuple[str, ...]
    pendingItems: tuple[str, ...]
    knownNotes: tuple[str, ...]
    unknownFields: tuple[str, ...]
    acquisitionCostLevel: CostLevel
    ongoingCareCostLevel: CostLevel
    sourceIds: tuple[str, ...]
    evidence: tuple[PublicEvidence, ...] = ()
    dataNature: DataNature
    listingStatus: ListingStatus
    merchant: PublicMerchantResult
    listingDisclosure: str
    contactAction: PublicContactAction


class PublicAINarrativeItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subjectId: str = Field(min_length=1)
    text: str = Field(min_length=1)


class PublicAINarrative(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intro: str = Field(min_length=1)
    items: tuple[PublicAINarrativeItem, ...]


class PublicRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    directions: tuple[PublicDirectionResult, ...]
    pets: tuple[PublicPetResult, ...]
    aiNarrative: PublicAINarrative | None = None
    priorityMessage: str | None = None
    petAvailabilityNote: str | None = None
    generalRisks: tuple[str, ...] = (
        "品种或类型只表示群体倾向，具体个体仍需继续了解",
        "平台不对宠物健康、性格或持续在售作绝对保证",
    )
    disclaimer: str = "咕噜港负责匹配并帮助联系商家进一步了解，不直接销售宠物。"


def load_catalog() -> Catalog:
    data_path = Path(__file__).parent.parent / "data"
    directions = json.loads((data_path / "directions.json").read_text(encoding="utf-8"))
    merchants = json.loads((data_path / "merchants.json").read_text(encoding="utf-8"))
    pets = json.loads((data_path / "pets.json").read_text(encoding="utf-8"))
    return Catalog(
        directions=TypeAdapter(tuple[DirectionProfile, ...]).validate_python(
            directions
        ),
        merchants=TypeAdapter(tuple[MerchantProfile, ...]).validate_python(merchants),
        pets=TypeAdapter(tuple[PetProfile, ...]).validate_python(pets),
    )


def score_assessments(assessments: tuple[FactorAssessment, ...]) -> CandidateScore:
    by_factor = {item.factor: item for item in assessments}
    if len(by_factor) != len(ScoringFactor) or set(by_factor) != set(ScoringFactor):
        raise ValueError("each scoring factor must appear exactly once")
    total = sum(
        FACTOR_WEIGHTS[factor] * by_factor[factor].ratio.value
        for factor in ScoringFactor
    )
    unknowns = tuple(
        factor
        for factor in ScoringFactor
        if by_factor[factor].status is SlotStatus.UNKNOWN
    )
    unresolved = any(
        by_factor[factor].ratio is FitRatio.MISMATCH
        for factor in RELATION_OR_LIFE_FACTORS
    )
    accepted = any(item.ratio is FitRatio.ADJUSTED for item in assessments)
    return CandidateScore(
        total=total,
        assessments=assessments,
        importantUnknowns=unknowns,
        unresolvedRelationshipOrLifeZero=unresolved,
        hasAcceptedCondition=accepted,
    )


def _slot_ratio(
    slot: SlotValue[Any],
    candidate_values: tuple[str, ...],
    *,
    accepted: bool = False,
    ordinal: bool = False,
) -> FitRatio:
    if slot.status in {SlotStatus.UNKNOWN, SlotStatus.DECLINED, SlotStatus.CONFLICTED}:
        return FitRatio.UNKNOWN
    raw = slot.value
    values = raw if isinstance(raw, tuple) else (raw,)
    normalized = tuple(str(value).upper() for value in values if value is not None)
    if not normalized:
        return FitRatio.UNKNOWN
    if any(value in _NEUTRAL_VALUES for value in normalized):
        return FitRatio.FULL
    candidates = tuple(value.upper() for value in candidate_values)
    if "ANY" in candidates:
        return FitRatio.FULL
    if set(normalized) & set(candidates):
        return FitRatio.FULL
    if ordinal and len(normalized) == 1 and len(candidates) == 1:
        wanted = _LEVEL_ORDER.get(normalized[0])
        actual = _LEVEL_ORDER.get(candidates[0])
        if wanted is not None and actual is not None and abs(wanted - actual) == 1:
            return FitRatio.ADJUSTED
    if accepted:
        return FitRatio.ADJUSTED
    return FitRatio.MISMATCH


def _assessment(
    factor: ScoringFactor,
    slot: SlotValue[Any],
    candidates: tuple[str, ...],
    accepted_slots: set[str],
    slot_name: str,
    *,
    ordinal: bool = False,
) -> FactorAssessment:
    ratio = _slot_ratio(
        slot,
        candidates,
        accepted=slot_name in accepted_slots,
        ordinal=ordinal,
    )
    reason = {
        FitRatio.FULL: "与已表达需求一致",
        FitRatio.ADJUSTED: "存在小幅差异，或用户已愿意为这一项调整",
        FitRatio.UNKNOWN: "用户尚未说明，按一半权重暂算并保持待确认",
        FitRatio.MISMATCH: "与已表达需求不一致",
    }[ratio]
    return FactorAssessment(
        factor=factor, ratio=ratio, status=slot.status, reason=reason
    )


def _time_demand(pet: PetProfile) -> str:
    if pet.interactionRhythm.value in {"HIGH", "MEDIUM_HIGH"}:
        return "HIGH"
    if pet.interactionRhythm.value == "MEDIUM":
        return "MEDIUM"
    return "LOW"


def _coat_tokens(pet: PetProfile) -> tuple[str, ...]:
    tokens = [pet.appearance.upper()]
    if "短毛" in pet.appearance:
        tokens.append("SHORT_HAIR")
    if "半长毛" in pet.appearance:
        tokens.append("SEMI_LONG_HAIR")
    if "卷毛" in pet.appearance:
        tokens.append("CURLY_HAIR")
    return tuple(tokens)


def _disturbance_tokens(pet: PetProfile) -> tuple[str, ...]:
    text = " ".join(pet.dailyCareNotes)
    shedding = "HIGH" if "明显" in text or "偏高" in text else "MEDIUM"
    noise = "MEDIUM" if "叫" in text else "LOW"
    return (f"SHEDDING_{shedding}", f"NOISE_{noise}")


def score_pet_candidate(
    profile: PetPreferenceProfile, pet: PetProfile
) -> CandidateScore:
    accepted_slots = set(profile.acceptedAdjustments.value or ())
    assessments = (
        _assessment(
            ScoringFactor.DIRECTION_SIZE,
            profile.directionAndSizePreference,
            (pet.directionId, pet.size),
            accepted_slots,
            "directionAndSizePreference",
        ),
        _assessment(
            ScoringFactor.AGE,
            profile.agePreference,
            (pet.ageStage,),
            accepted_slots,
            "agePreference",
        ),
        _assessment(
            ScoringFactor.COAT_APPEARANCE,
            profile.coatAppearancePreference,
            _coat_tokens(pet),
            accepted_slots,
            "coatAppearancePreference",
        ),
        _assessment(
            ScoringFactor.INTERACTION_RHYTHM,
            profile.interactionRhythm,
            (pet.interactionRhythm.value,),
            accepted_slots,
            "interactionRhythm",
            ordinal=True,
        ),
        _assessment(
            ScoringFactor.COMPANIONSHIP_DISTANCE,
            profile.companionshipDistance,
            (pet.companionshipDistance,),
            accepted_slots,
            "companionshipDistance",
        ),
        _assessment(
            ScoringFactor.CURRENT_TIME,
            profile.currentTimeArrangement,
            (_time_demand(pet),),
            accepted_slots,
            "currentTimeArrangement",
            ordinal=True,
        ),
        _assessment(
            ScoringFactor.ONGOING_INVESTMENT,
            profile.ongoingInvestmentWillingness,
            (pet.ongoingCareCostLevel.value,),
            accepted_slots,
            "ongoingInvestmentWillingness",
            ordinal=True,
        ),
        _assessment(
            ScoringFactor.DISTURBANCE_TOLERANCE,
            profile.disturbanceTolerance,
            _disturbance_tokens(pet),
            accepted_slots,
            "disturbanceTolerance",
        ),
    )
    return score_assessments(assessments)


def _direction_assessment(
    factor: ScoringFactor,
    slot: SlotValue[Any],
    candidates: tuple[str, ...],
    accepted_slots: set[str],
    slot_name: str,
    *,
    ordinal: bool = False,
) -> FactorAssessment:
    assessment = _assessment(
        factor,
        slot,
        candidates,
        accepted_slots,
        slot_name,
        ordinal=ordinal,
    )
    if assessment.ratio is not FitRatio.MISMATCH or "VARIABLE" not in candidates:
        return assessment
    return FactorAssessment(
        factor=factor,
        ratio=FitRatio.UNKNOWN,
        status=slot.status,
        reason="这个方向的群体差异较大，需要再看具体宠物档案",
    )


def score_direction_candidate(
    profile: PetPreferenceProfile,
    direction: DirectionProfile,
) -> CandidateScore:
    accepted_slots = set(profile.acceptedAdjustments.value or ())
    traits = direction.matchTraits
    assessments = (
        _direction_assessment(
            ScoringFactor.DIRECTION_SIZE,
            profile.directionAndSizePreference,
            (direction.directionId, *traits.sizeOptions),
            accepted_slots,
            "directionAndSizePreference",
        ),
        _direction_assessment(
            ScoringFactor.AGE,
            profile.agePreference,
            traits.ageStages,
            accepted_slots,
            "agePreference",
        ),
        _direction_assessment(
            ScoringFactor.COAT_APPEARANCE,
            profile.coatAppearancePreference,
            traits.coatAppearanceOptions,
            accepted_slots,
            "coatAppearancePreference",
        ),
        _direction_assessment(
            ScoringFactor.INTERACTION_RHYTHM,
            profile.interactionRhythm,
            traits.interactionRhythms,
            accepted_slots,
            "interactionRhythm",
            ordinal=True,
        ),
        _direction_assessment(
            ScoringFactor.COMPANIONSHIP_DISTANCE,
            profile.companionshipDistance,
            traits.companionshipDistances,
            accepted_slots,
            "companionshipDistance",
        ),
        _direction_assessment(
            ScoringFactor.CURRENT_TIME,
            profile.currentTimeArrangement,
            traits.timeDemandLevels,
            accepted_slots,
            "currentTimeArrangement",
            ordinal=True,
        ),
        _direction_assessment(
            ScoringFactor.ONGOING_INVESTMENT,
            profile.ongoingInvestmentWillingness,
            traits.ongoingInvestmentLevels,
            accepted_slots,
            "ongoingInvestmentWillingness",
            ordinal=True,
        ),
        _direction_assessment(
            ScoringFactor.DISTURBANCE_TOLERANCE,
            profile.disturbanceTolerance,
            traits.disturbanceLevels,
            accepted_slots,
            "disturbanceTolerance",
        ),
    )
    return score_assessments(assessments)


def determine_match_level(candidate: InternalCandidate) -> MatchLevel | None:
    if candidate.hardExcluded:
        return None
    if candidate.internalScore < 60:
        return None
    if candidate.unresolvedRelationshipOrLifeZero:
        return MatchLevel.CAUTION
    if (
        candidate.internalScore < 80
        or candidate.pendingItems
        or candidate.hasAcceptedCondition
        or candidate.hasSmallDifference
    ):
        return MatchLevel.MEDIUM
    return MatchLevel.HIGH


def rank_internal_candidates(
    candidates: tuple[InternalCandidate, ...],
) -> tuple[InternalCandidate, ...]:
    level_order = {MatchLevel.HIGH: 0, MatchLevel.MEDIUM: 1, MatchLevel.CAUTION: 2}
    visible = [item for item in candidates if item.matchLevel is not None]

    def rank_key(item: InternalCandidate) -> tuple[int, float, str]:
        level = item.matchLevel
        assert level is not None
        return (level_order[level], -item.internalScore, item.targetId)

    return tuple(sorted(visible, key=rank_key))


def _species_allowed(profile: PetPreferenceProfile, pet: PetProfile) -> bool:
    scope = profile.speciesScope
    if scope.status is SlotStatus.CONFIRMED and scope.value:
        allowed = {value.upper() for value in scope.value}
        if "ANY" not in allowed and pet.species.value not in allowed:
            return False
    allergies = profile.allergySpecies
    return not (
        allergies.status is SlotStatus.CONFIRMED
        and allergies.value
        and pet.species.value in {value.upper() for value in allergies.value}
    )


def _violates_bottom_line(profile: PetPreferenceProfile, pet: PetProfile) -> bool:
    slot = profile.absoluteBottomLines
    if slot.status is not SlotStatus.CONFIRMED or not slot.value:
        return False
    notes = " ".join(pet.dailyCareNotes)
    for rule in slot.value:
        if rule == "SHEDDING_MAX:LOW" and ("掉毛" in notes and "较少" not in notes):
            return True
        if rule == "NOISE_MAX:LOW" and "叫" in notes:
            return True
    return False


def _direction_species_allowed(
    profile: PetPreferenceProfile,
    direction: DirectionProfile,
) -> bool:
    scope = profile.speciesScope
    if scope.status is SlotStatus.CONFIRMED and scope.value:
        allowed = {value.upper() for value in scope.value}
        if "ANY" not in allowed and direction.species.value not in allowed:
            return False
    allergies = profile.allergySpecies
    return not (
        allergies.status is SlotStatus.CONFIRMED
        and allergies.value
        and direction.species.value in {value.upper() for value in allergies.value}
    )


def _direction_violates_bottom_line(
    profile: PetPreferenceProfile,
    direction: DirectionProfile,
) -> bool:
    slot = profile.absoluteBottomLines
    if slot.status is not SlotStatus.CONFIRMED or not slot.value:
        return False
    disturbance = set(direction.matchTraits.disturbanceLevels)
    for rule in slot.value:
        if rule == "SHEDDING_MAX:LOW" and disturbance.intersection(
            {"SHEDDING_MEDIUM", "SHEDDING_MEDIUM_HIGH", "SHEDDING_HIGH"}
        ):
            return True
        if rule == "NOISE_MAX:LOW" and disturbance.intersection(
            {"NOISE_MEDIUM", "NOISE_MEDIUM_HIGH", "NOISE_HIGH"}
        ):
            return True
    return False


def match_direction_candidates(
    profile: PetPreferenceProfile,
    directions: tuple[DirectionProfile, ...],
) -> tuple[InternalCandidate, ...]:
    candidates: list[InternalCandidate] = []
    for direction in directions:
        if not _direction_species_allowed(profile, direction):
            continue
        if _direction_violates_bottom_line(profile, direction):
            continue
        score = score_direction_candidate(profile, direction)
        candidates.append(
            InternalCandidate(
                targetId=direction.directionId,
                directionId=direction.directionId,
                internalScore=score.total,
                mismatchPoints=tuple(
                    item.reason
                    for item in score.assessments
                    if item.ratio is FitRatio.MISMATCH
                ),
                suitableReasons=direction.suitableConditions,
                tradeoffs=(
                    *direction.typicalBurdens,
                    *direction.healthCareRisks,
                    *direction.nonGuarantees,
                ),
                pendingItems=tuple(item.value for item in score.importantUnknowns),
                unresolvedRelationshipOrLifeZero=(
                    score.unresolvedRelationshipOrLifeZero
                ),
                hasAcceptedCondition=score.hasAcceptedCondition,
                hasSmallDifference=score.hasAcceptedCondition,
                fullyInformed=not score.importantUnknowns,
            )
        )
    return rank_internal_candidates(tuple(candidates))


def match_pet_candidates(
    profile: PetPreferenceProfile,
    pets: tuple[PetProfile, ...],
) -> tuple[InternalCandidate, ...]:
    candidates: list[InternalCandidate] = []
    for pet in pets:
        if not _species_allowed(profile, pet) or _violates_bottom_line(profile, pet):
            continue
        score = score_pet_candidate(profile, pet)
        mismatch_points = tuple(
            item.reason for item in score.assessments if item.ratio is FitRatio.MISMATCH
        )
        suitable_reasons = tuple(
            item.reason for item in score.assessments if item.ratio is FitRatio.FULL
        )
        candidates.append(
            InternalCandidate(
                targetId=pet.petId,
                directionId=pet.directionId,
                internalScore=score.total,
                mismatchPoints=mismatch_points,
                suitableReasons=suitable_reasons,
                tradeoffs=pet.knownNotes,
                pendingItems=tuple(item.value for item in score.importantUnknowns),
                unresolvedRelationshipOrLifeZero=score.unresolvedRelationshipOrLifeZero,
                hasAcceptedCondition=score.hasAcceptedCondition,
                hasSmallDifference=score.hasAcceptedCondition,
                fullyInformed=not score.importantUnknowns,
            )
        )
    return rank_internal_candidates(tuple(candidates))


def _select_unique_directions(
    candidates: tuple[InternalCandidate, ...],
) -> tuple[InternalCandidate, ...]:
    selected: list[InternalCandidate] = []
    seen: set[str] = set()
    for candidate in rank_internal_candidates(candidates):
        if candidate.directionId in seen:
            continue
        selected.append(candidate)
        seen.add(candidate.directionId)
        if len(selected) == 4:
            break
    return tuple(selected)


def build_public_recommendation(
    catalog: Catalog,
    direction_candidates: tuple[InternalCandidate, ...],
    pet_candidates: tuple[InternalCandidate, ...],
    knowledge_entries: tuple[KnowledgeEntry, ...] = (),
) -> PublicRecommendation:
    direction_map = {item.directionId: item for item in catalog.directions}
    merchant_map = {item.merchantId: item for item in catalog.merchants}
    pet_map = {item.petId: item for item in catalog.pets}
    knowledge_map = {item.sourceId: item for item in knowledge_entries}

    def evidence(source_ids: tuple[str, ...]) -> tuple[PublicEvidence, ...]:
        return tuple(
            PublicEvidence(
                sourceId=entry.sourceId,
                sourceName=entry.sourceName,
                sourceLocator=entry.sourceLocator,
            )
            for source_id in source_ids
            if (entry := knowledge_map.get(source_id)) is not None
        )

    selected_directions = _select_unique_directions(direction_candidates)
    selected_direction_ids = {item.directionId for item in selected_directions}

    public_directions: list[PublicDirectionResult] = []
    for candidate in selected_directions:
        direction = direction_map.get(candidate.directionId)
        level = candidate.matchLevel
        if direction is None or level is None:
            continue
        public_directions.append(
            PublicDirectionResult(
                directionId=direction.directionId,
                name=direction.name,
                kind=direction.kind,
                matchLevel=level,
                suitableReasons=candidate.suitableReasons
                or direction.suitableConditions,
                tradeoffs=candidate.tradeoffs or direction.typicalBurdens,
                mismatchPoints=candidate.mismatchPoints,
                pendingItems=candidate.pendingItems,
                acquisitionCostLevel=direction.acquisitionCostLevel,
                ongoingCareCostLevel=direction.ongoingCareCostLevel,
                sourceIds=direction.sourceIds,
                evidence=evidence(direction.sourceIds),
                evidenceNote="群体倾向不代表具体个体",
            )
        )

    eligible_pets = tuple(
        item for item in pet_candidates if item.directionId in selected_direction_ids
    )
    selected_pets = _select_unique_directions(eligible_pets)
    public_pets: list[PublicPetResult] = []
    for candidate in selected_pets:
        pet = pet_map.get(candidate.targetId)
        level = candidate.matchLevel
        if pet is None or level is None:
            continue
        merchant = merchant_map[pet.merchantId]
        public_pets.append(
            PublicPetResult(
                petId=pet.petId,
                nickname=pet.nickname,
                directionId=pet.directionId,
                matchLevel=level,
                suitableReasons=candidate.suitableReasons,
                tradeoffs=candidate.tradeoffs,
                mismatchPoints=candidate.mismatchPoints,
                pendingItems=candidate.pendingItems,
                knownNotes=pet.knownNotes,
                unknownFields=pet.unknownFields,
                acquisitionCostLevel=pet.acquisitionCostLevel,
                ongoingCareCostLevel=pet.ongoingCareCostLevel,
                sourceIds=pet.sourceIds,
                evidence=evidence(pet.sourceIds),
                dataNature=pet.dataNature,
                listingStatus=pet.listingStatus,
                merchant=PublicMerchantResult(
                    merchantId=merchant.merchantId,
                    displayName=merchant.displayName,
                ),
                listingDisclosure=pet.disclosure,
                contactAction=PublicContactAction(),
            )
        )

    levels = [pet.matchLevel for pet in public_pets]
    priority_message = None
    if levels:
        priority_message = (
            "目前没有特别合拍的选择，先看看相对更接近的伙伴"
            if all(level is MatchLevel.CAUTION for level in levels)
            else "先认识排在前面的伙伴"
        )
    note = None
    if not public_pets:
        note = (
            "当前Demo档案暂无合适个体"
            if public_directions
            else "按你现在告诉我的条件，还没有特别合适的选择"
        )
    return PublicRecommendation(
        directions=tuple(public_directions),
        pets=tuple(public_pets),
        priorityMessage=priority_message,
        petAvailabilityNote=note,
    )
