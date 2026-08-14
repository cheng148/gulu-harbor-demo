from collections import Counter

from app.domain.catalog import DEMO_DISCLOSURE, DataNature, ListingStatus
from app.domain.matching import load_catalog

DIRECTION_PETS = {
    "cat-adult-local-mix": {"小麦", "栗子"},
    "cat-british-shorthair": {"年糕", "奶盖"},
    "cat-american-shorthair": {"花生", "星星"},
    "cat-ragdoll": {"糯米", "蓝莓"},
    "dog-adult-local-mix": {"阿福", "豆包"},
    "dog-toy-mini-poodle": {"可可", "泡芙"},
    "dog-pembroke-corgi": {"土豆", "团子"},
    "dog-labrador-retriever": {"大麦", "乌龙"},
}

MERCHANT_PETS = {
    "merchant-harbor": {"小麦", "年糕", "花生", "糯米", "阿福", "可可", "土豆", "大麦"},
    "merchant-cloud": {"栗子", "奶盖", "星星", "蓝莓", "豆包", "泡芙", "团子", "乌龙"},
}


def test_catalog_contains_only_the_approved_directions_pets_and_merchants() -> None:
    catalog = load_catalog()

    assert len(catalog.directions) == 8
    assert len(catalog.pets) == 16
    assert len(catalog.merchants) == 2
    assert {item.directionId for item in catalog.directions} == set(DIRECTION_PETS)
    assert {item.nickname for item in catalog.pets} == set().union(*DIRECTION_PETS.values())
    assert {item.displayName for item in catalog.merchants} == {
        "港湾宠物生活馆（模拟线下商家）",
        "云朵宠物屋（模拟线上商家）",
    }


def test_each_direction_has_its_two_approved_pets() -> None:
    catalog = load_catalog()

    actual = {
        direction_id: {pet.nickname for pet in catalog.pets if pet.directionId == direction_id}
        for direction_id in DIRECTION_PETS
    }
    assert actual == DIRECTION_PETS


def test_each_merchant_has_eight_approved_pets() -> None:
    catalog = load_catalog()

    actual = {
        merchant_id: {pet.nickname for pet in catalog.pets if pet.merchantId == merchant_id}
        for merchant_id in MERCHANT_PETS
    }
    assert actual == MERCHANT_PETS
    assert Counter(pet.merchantId for pet in catalog.pets) == {
        "merchant-harbor": 8,
        "merchant-cloud": 8,
    }


def test_every_pet_is_explicitly_simulated_available_and_has_unknown_fields() -> None:
    catalog = load_catalog()

    assert all(pet.dataNature is DataNature.DEMO_SIMULATED for pet in catalog.pets)
    assert all(pet.listingStatus is ListingStatus.SIMULATED_AVAILABLE for pet in catalog.pets)
    assert all(pet.disclosure == DEMO_DISCLOSURE for pet in catalog.pets)
    assert all(pet.unknownFields for pet in catalog.pets)
    assert all(pet.merchantId in {merchant.merchantId for merchant in catalog.merchants} for pet in catalog.pets)