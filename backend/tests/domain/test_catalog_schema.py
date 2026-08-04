from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.catalog import Catalog, DirectionProfile, PetProfile, Species
from app.domain.knowledge import KnowledgeEntry


def direction_payload() -> dict[str, object]:
    return {
        "directionId": "cat-adult-mixed",
        "name": "成年混种猫",
        "kind": "TYPE",
        "species": "CAT",
        "tendencies": ["成年个体的行为观察通常比幼年阶段更稳定"],
        "suitableConditions": ["希望个体信息较明确"],
        "typicalBurdens": ["仍可能掉毛和抓挠"],
        "healthCareRisks": ["需要常规体检和疫苗咨询"],
        "nonGuarantees": ["类型倾向不代表具体个体"],
        "monthlyCostCny": {"minimum": 300, "maximum": 800},
        "sourceIds": ["source-cat-care"],
    }


def pet_payload() -> dict[str, object]:
    return {
        "petId": "pet-cat-001",
        "nickname": "栗子",
        "directionId": "cat-adult-mixed",
        "species": "CAT",
        "ageStage": "ADULT",
        "sex": "FEMALE",
        "size": "SMALL",
        "activityLevel": "LOW",
        "minimumExerciseMinutes": 20,
        "minimumCompanionHours": 2,
        "maximumAloneHours": 8,
        "sheddingLevel": "MEDIUM",
        "noiseLevel": "LOW",
        "odorLevel": "LOW",
        "groomingLevel": "LOW",
        "experienceRequired": "BEGINNER",
        "monthlyCostCny": {"minimum": 350, "maximum": 700},
        "suitableTags": ["APARTMENT", "OLDER_ADULTS"],
        "unsuitableTags": ["TODDLERS"],
        "observationSource": "FOSTER_NOTES",
        "observationPeriodDays": 21,
        "knownNotes": ["初见陌生人会躲藏"],
        "listingType": "ADOPTION",
        "sourceIds": ["source-cat-care"],
        "imageRef": "placeholder://pet-cat-001",
    }


def test_catalog_keeps_direction_and_specific_pet_as_two_layers() -> None:
    direction = DirectionProfile.model_validate(direction_payload())
    pet = PetProfile.model_validate(pet_payload())
    catalog = Catalog(directions=(direction,), pets=(pet,))

    assert catalog.directions[0].directionId == pet.directionId
    assert catalog.pets[0].petId == "pet-cat-001"


def test_catalog_rejects_pet_linked_to_missing_direction() -> None:
    pet = PetProfile.model_validate({**pet_payload(), "directionId": "missing"})

    with pytest.raises(ValidationError):
        Catalog(
            directions=(DirectionProfile.model_validate(direction_payload()),),
            pets=(pet,),
        )


def test_direction_and_pet_require_traceable_sources() -> None:
    with pytest.raises(ValidationError):
        DirectionProfile.model_validate({**direction_payload(), "sourceIds": []})
    with pytest.raises(ValidationError):
        PetProfile.model_validate({**pet_payload(), "sourceIds": []})

def test_pet_requires_an_explicit_image_source_or_placeholder() -> None:
    payload = pet_payload()
    del payload["imageRef"]

    with pytest.raises(ValidationError):
        PetProfile.model_validate(payload)


def test_knowledge_entry_requires_boundary_and_review_date() -> None:
    with pytest.raises(ValidationError):
        KnowledgeEntry(
            sourceId="source-cat-care",
            title="猫日常照护",
            topic="CARE",
            appliesTo=(Species.CAT,),
            rewrittenBody="需要稳定饮水、饮食和常规健康检查。",
            sourceName="公开照护资料的演示性改写",
            sourceLocator="internal-reference",
            publicationDate=None,
            publicationDateUnknown=True,
            localReviewDate=date(2026, 8, 4),
            applicabilityBoundary="",
        )
