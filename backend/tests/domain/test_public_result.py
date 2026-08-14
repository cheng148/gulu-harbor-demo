from app.domain.matching import (
    InternalCandidate,
    MatchLevel,
    build_public_recommendation,
    load_catalog,
)


def item(
    target: str,
    direction: str,
    score: float,
    *,
    caution: bool = False,
    pending: tuple[str, ...] = (),
) -> InternalCandidate:
    return InternalCandidate(
        targetId=target,
        directionId=direction,
        internalScore=score,
        suitableReasons=("相处节奏接近",),
        tradeoffs=("仍需继续了解",),
        mismatchPoints=("日常时间需要磨合",) if caution else (),
        pendingItems=pending,
        unresolvedRelationshipOrLifeZero=caution,
    )


def test_public_result_has_no_internal_score_and_includes_merchant_demo_boundary() -> None:
    catalog = load_catalog()
    direction = item("cat-adult-local-mix", "cat-adult-local-mix", 82)
    pet = item("pet-cat-local-01", "cat-adult-local-mix", 82)

    result = build_public_recommendation(catalog, (direction,), (pet,))
    payload = result.model_dump_json()

    assert result.pets[0].matchLevel is MatchLevel.HIGH
    assert result.pets[0].merchant.displayName == "港湾宠物生活馆（模拟线下商家）"
    assert result.pets[0].listingDisclosure == "Demo模拟数据，不代表真实在售"
    assert result.pets[0].contactAction.available is False
    assert result.pets[0].contactAction.unavailableMessage == "Demo演示功能，暂未开放。"
    for forbidden in ("internalScore", "matchScore", "rawScore", "monthlyCostCny"):
        assert forbidden not in payload


def test_public_result_is_limited_to_four_and_one_pet_per_direction() -> None:
    catalog = load_catalog()
    directions = tuple(
        item(direction.directionId, direction.directionId, 90 - index)
        for index, direction in enumerate(catalog.directions[:5])
    )
    pets = (
        item("pet-cat-local-02", "cat-adult-local-mix", 99),
        item("pet-cat-local-01", "cat-adult-local-mix", 98),
        item("pet-cat-british-01", "cat-british-shorthair", 91),
        item("pet-cat-american-01", "cat-american-shorthair", 90),
        item("pet-cat-ragdoll-01", "cat-ragdoll", 89),
        item("pet-dog-local-01", "dog-adult-local-mix", 88),
    )

    result = build_public_recommendation(catalog, directions, pets)

    assert len(result.directions) == 4
    assert len(result.pets) == 4
    assert len({pet.directionId for pet in result.pets}) == 4
    assert [pet.petId for pet in result.pets[:2]] == [
        "pet-cat-local-02",
        "pet-cat-british-01",
    ]
    assert all(pet.matchLevel is MatchLevel.HIGH for pet in result.pets)


def test_all_caution_results_never_claim_priority_recommendation() -> None:
    catalog = load_catalog()
    direction = item("cat-adult-local-mix", "cat-adult-local-mix", 90, caution=True)
    pet = item("pet-cat-local-01", "cat-adult-local-mix", 90, caution=True)

    result = build_public_recommendation(catalog, (direction,), (pet,))

    assert result.pets[0].matchLevel is MatchLevel.CAUTION
    assert "优先推荐" not in (result.priorityMessage or "")
    assert result.priorityMessage == "目前没有特别合拍的选择，先看看相对更接近的伙伴"


def test_direction_can_be_returned_without_inventing_a_pet() -> None:
    catalog = load_catalog()
    direction = item("cat-ragdoll", "cat-ragdoll", 70)

    result = build_public_recommendation(catalog, (direction,), ())

    assert len(result.directions) == 1
    assert result.pets == ()
    assert result.petAvailabilityNote == "当前Demo档案暂无合适个体"