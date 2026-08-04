from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Species(StrEnum):
    CAT = "CAT"
    DOG = "DOG"


class DirectionKind(StrEnum):
    BREED = "BREED"
    TYPE = "TYPE"


class Level(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CostRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    minimum: int = Field(ge=0)
    maximum: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> CostRange:
        if self.maximum < self.minimum:
            raise ValueError("maximum cost cannot be below minimum cost")
        return self


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
    monthlyCostCny: CostRange
    sourceIds: tuple[str, ...] = Field(min_length=1)


class PetProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    petId: str = Field(min_length=1)
    nickname: str = Field(min_length=1)
    directionId: str = Field(min_length=1)
    species: Species
    ageStage: str = Field(min_length=1)
    sex: str = Field(min_length=1)
    size: str = Field(min_length=1)
    activityLevel: Level
    minimumExerciseMinutes: int = Field(ge=0)
    minimumCompanionHours: float = Field(ge=0, le=24)
    maximumAloneHours: float = Field(ge=0, le=24)
    sheddingLevel: Level
    noiseLevel: Level
    odorLevel: Level
    groomingLevel: Level
    experienceRequired: str = Field(min_length=1)
    monthlyCostCny: CostRange
    suitableTags: tuple[str, ...]
    unsuitableTags: tuple[str, ...]
    observationSource: str = Field(min_length=1)
    observationPeriodDays: int = Field(gt=0)
    knownNotes: tuple[str, ...]
    listingType: str = Field(min_length=1)
    sourceIds: tuple[str, ...] = Field(min_length=1)
    imageRef: str = Field(min_length=1)


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    directions: tuple[DirectionProfile, ...]
    pets: tuple[PetProfile, ...]

    @model_validator(mode="after")
    def validate_links_and_uniqueness(self) -> Catalog:
        direction_map = {item.directionId: item for item in self.directions}
        if len(direction_map) != len(self.directions):
            raise ValueError("direction IDs must be unique")
        if len({item.petId for item in self.pets}) != len(self.pets):
            raise ValueError("pet IDs must be unique")
        for pet in self.pets:
            direction = direction_map.get(pet.directionId)
            if direction is None:
                raise ValueError(f"pet {pet.petId} links to a missing direction")
            if direction.species is not pet.species:
                raise ValueError(f"pet {pet.petId} species differs from its direction")
        return self
