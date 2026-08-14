from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEMO_DISCLOSURE = "Demo模拟数据，不代表真实在售"


class Species(StrEnum):
    CAT = "CAT"
    DOG = "DOG"


class DirectionKind(StrEnum):
    BREED = "BREED"
    TYPE = "TYPE"


class Level(StrEnum):
    LOW = "LOW"
    LOW_MEDIUM = "LOW_MEDIUM"
    MEDIUM = "MEDIUM"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    HIGH = "HIGH"


class CostLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    MEDIUM_HIGH = "MEDIUM_HIGH"
    HIGH = "HIGH"


class DataNature(StrEnum):
    DEMO_SIMULATED = "DEMO_SIMULATED"


class ListingStatus(StrEnum):
    SIMULATED_AVAILABLE = "SIMULATED_AVAILABLE"


class MerchantType(StrEnum):
    SIMULATED_OFFLINE = "SIMULATED_OFFLINE"
    SIMULATED_ONLINE = "SIMULATED_ONLINE"


class MerchantProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    merchantId: str = Field(min_length=1)
    displayName: str = Field(min_length=1)
    merchantType: MerchantType
    dataNature: DataNature
    disclosure: str = Field(min_length=1)
    contactActionAvailable: bool

    @model_validator(mode="after")
    def validate_demo_boundary(self) -> MerchantProfile:
        if self.disclosure != DEMO_DISCLOSURE:
            raise ValueError("simulated merchant must use the approved disclosure")
        if self.contactActionAvailable:
            raise ValueError("merchant contact is unavailable in the Demo")
        return self


class DirectionMatchTraits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sizeOptions: tuple[str, ...] = Field(min_length=1)
    ageStages: tuple[str, ...] = Field(min_length=1)
    coatAppearanceOptions: tuple[str, ...] = Field(min_length=1)
    interactionRhythms: tuple[str, ...] = Field(min_length=1)
    companionshipDistances: tuple[str, ...] = Field(min_length=1)
    timeDemandLevels: tuple[str, ...] = Field(min_length=1)
    ongoingInvestmentLevels: tuple[str, ...] = Field(min_length=1)
    disturbanceLevels: tuple[str, ...] = Field(min_length=1)


class DirectionProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    directionId: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: DirectionKind
    species: Species
    tendencies: tuple[str, ...] = Field(min_length=1)
    suitableConditions: tuple[str, ...] = Field(min_length=1)
    typicalBurdens: tuple[str, ...] = Field(min_length=1)
    healthCareRisks: tuple[str, ...] = Field(min_length=1)
    nonGuarantees: tuple[str, ...] = Field(min_length=1)
    matchTraits: DirectionMatchTraits
    acquisitionCostLevel: CostLevel
    ongoingCareCostLevel: CostLevel
    sourceIds: tuple[str, ...] = Field(min_length=1)


class PetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    petId: str = Field(min_length=1)
    nickname: str = Field(min_length=1)
    directionId: str = Field(min_length=1)
    merchantId: str = Field(min_length=1)
    species: Species
    ageStage: str = Field(min_length=1)
    ageDisplay: str = Field(min_length=1)
    size: str = Field(min_length=1)
    appearance: str = Field(min_length=1)
    observedPersonality: str = Field(min_length=1)
    interactionRhythm: Level
    companionshipDistance: str = Field(min_length=1)
    aloneTimeObservation: str = Field(min_length=1)
    dailyCareNotes: tuple[str, ...] = Field(min_length=1)
    acquisitionCostLevel: CostLevel
    ongoingCareCostLevel: CostLevel
    knownNotes: tuple[str, ...] = Field(min_length=1)
    unknownFields: tuple[str, ...]
    observationSource: str = Field(min_length=1)
    observationPeriodDays: int = Field(gt=0)
    dataNature: DataNature
    listingStatus: ListingStatus
    disclosure: str = Field(min_length=1)
    sourceIds: tuple[str, ...] = Field(min_length=1)
    imageRef: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_demo_boundary(self) -> PetProfile:
        if self.disclosure != DEMO_DISCLOSURE:
            raise ValueError("simulated pet must use the approved disclosure")
        return self


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    directions: tuple[DirectionProfile, ...]
    merchants: tuple[MerchantProfile, ...]
    pets: tuple[PetProfile, ...]

    @model_validator(mode="after")
    def validate_links_and_uniqueness(self) -> Catalog:
        direction_map = {item.directionId: item for item in self.directions}
        merchant_ids = {item.merchantId for item in self.merchants}
        if len(direction_map) != len(self.directions):
            raise ValueError("direction IDs must be unique")
        if len(merchant_ids) != len(self.merchants):
            raise ValueError("merchant IDs must be unique")
        if len({item.petId for item in self.pets}) != len(self.pets):
            raise ValueError("pet IDs must be unique")
        for pet in self.pets:
            direction = direction_map.get(pet.directionId)
            if direction is None:
                raise ValueError(f"pet {pet.petId} links to a missing direction")
            if pet.merchantId not in merchant_ids:
                raise ValueError(f"pet {pet.petId} links to a missing merchant")
            if direction.species is not pet.species:
                raise ValueError(f"pet {pet.petId} species differs from its direction")
        return self
