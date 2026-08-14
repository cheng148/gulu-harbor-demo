from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.catalog import (
    Catalog,
    DirectionProfile,
    MerchantProfile,
    PetProfile,
    Species,
)
from app.domain.knowledge import KnowledgeEntry

DISCLOSURE = "Demo模拟数据，不代表真实在售"


def merchant_payload() -> dict[str, object]:
    return {
        "merchantId": "merchant-harbor",
        "displayName": "港湾宠物生活馆（模拟线下商家）",
        "merchantType": "SIMULATED_OFFLINE",
        "dataNature": "DEMO_SIMULATED",
        "disclosure": DISCLOSURE,
        "contactActionAvailable": False,
    }


def direction_payload() -> dict[str, object]:
    return {
        "directionId": "cat-adult-local-mix",
        "name": "成年本地／混种短毛猫",
        "kind": "TYPE",
        "species": "CAT",
        "tendencies": ["优先使用成年后的实际行为记录"],
        "suitableConditions": ["愿意依据个体记录选择"],
        "typicalBurdens": ["仍会掉毛"],
        "healthCareRisks": ["健康资料需要进一步核实"],
        "nonGuarantees": ["不保证统一性格或健康"],
        "matchTraits": {
            "sizeOptions": ["VARIABLE"],
            "ageStages": ["ADULT"],
            "coatAppearanceOptions": ["SHORT_HAIR"],
            "interactionRhythms": ["VARIABLE"],
            "companionshipDistances": ["VARIABLE"],
            "timeDemandLevels": ["VARIABLE"],
            "ongoingInvestmentLevels": ["MEDIUM"],
            "disturbanceLevels": ["VARIABLE"],
        },
        "acquisitionCostLevel": "LOW",
        "ongoingCareCostLevel": "MEDIUM",
        "sourceIds": ["source-cat-care"],
    }


def pet_payload() -> dict[str, object]:
    return {
        "petId": "pet-cat-local-01",
        "nickname": "小麦",
        "directionId": "cat-adult-local-mix",
        "merchantId": "merchant-harbor",
        "species": "CAT",
        "ageStage": "ADULT",
        "ageDisplay": "3岁",
        "size": "MEDIUM",
        "appearance": "橘白短毛",
        "observedPersonality": "安静慢热",
        "interactionRhythm": "LOW_MEDIUM",
        "companionshipDistance": "NEARBY",
        "aloneTimeObservation": "短时间独处观察较稳定，完整工作日未知",
        "dailyCareNotes": ["中等掉毛", "梳理负担较低"],
        "acquisitionCostLevel": "LOW",
        "ongoingCareCostLevel": "MEDIUM",
        "knownNotes": ["换环境后可能暂时躲藏"],
        "unknownFields": ["完整工作日独处表现"],
        "observationSource": "SIMULATED_OFFLINE_OBSERVATION",
        "observationPeriodDays": 28,
        "dataNature": "DEMO_SIMULATED",
        "listingStatus": "SIMULATED_AVAILABLE",
        "disclosure": DISCLOSURE,
        "sourceIds": ["source-cat-care"],
        "imageRef": "placeholder://pet-cat-local-01",
    }


def make_catalog() -> Catalog:
    return Catalog(
        directions=(DirectionProfile.model_validate(direction_payload()),),
        merchants=(MerchantProfile.model_validate(merchant_payload()),),
        pets=(PetProfile.model_validate(pet_payload()),),
    )


def test_catalog_keeps_direction_pet_and_merchant_as_three_layers() -> None:
    catalog = make_catalog()
    assert catalog.pets[0].directionId == catalog.directions[0].directionId
    assert catalog.pets[0].merchantId == catalog.merchants[0].merchantId


def test_catalog_rejects_pet_linked_to_missing_merchant() -> None:
    with pytest.raises(ValidationError):
        Catalog(
            directions=(DirectionProfile.model_validate(direction_payload()),),
            merchants=(MerchantProfile.model_validate(merchant_payload()),),
            pets=(
                PetProfile.model_validate({**pet_payload(), "merchantId": "missing"}),
            ),
        )


def test_demo_pet_requires_simulated_nature_listing_and_exact_disclosure() -> None:
    for field, invalid in (
        ("dataNature", "REAL"),
        ("listingStatus", "AVAILABLE"),
        ("disclosure", "在售"),
    ):
        with pytest.raises(ValidationError):
            PetProfile.model_validate({**pet_payload(), field: invalid})


def test_catalog_rejects_exact_monthly_cost_fields() -> None:
    with pytest.raises(ValidationError):
        DirectionProfile.model_validate(
            {**direction_payload(), "monthlyCostCny": {"minimum": 300, "maximum": 800}}
        )
    with pytest.raises(ValidationError):
        PetProfile.model_validate(
            {**pet_payload(), "monthlyCostCny": {"minimum": 300, "maximum": 800}}
        )


def test_direction_and_pet_require_sources_and_explicit_unknowns() -> None:
    with pytest.raises(ValidationError):
        DirectionProfile.model_validate({**direction_payload(), "sourceIds": []})
    with pytest.raises(ValidationError):
        PetProfile.model_validate({**pet_payload(), "sourceIds": []})
    payload = pet_payload()
    del payload["unknownFields"]
    with pytest.raises(ValidationError):
        PetProfile.model_validate(payload)


def test_merchant_contact_is_demo_only() -> None:
    with pytest.raises(ValidationError):
        MerchantProfile.model_validate(
            {**merchant_payload(), "contactActionAvailable": True}
        )


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
