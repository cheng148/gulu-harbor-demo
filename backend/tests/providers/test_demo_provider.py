from app.domain.profile_merge import ProfileDelta
from app.providers.base import ProfileExtractionRequest, QuestionWordingRequest
from app.providers.demo import DemoMockProvider


def test_demo_provider_extracts_the_approved_five_turn_scenario() -> None:
    provider = DemoMockProvider()
    turns = (
        (
            "我想认识一只成年英国短毛猫，偏中等体型和短毛。",
            {"speciesScope", "directionAndSizePreference", "agePreference", "coatAppearancePreference"},
        ),
        ("工作日能留出一些时间，希望活动量不用太高。", {"currentTimeArrangement"}),
        ("我喜欢安静一点的互动，待在附近陪着就很好。", {"interactionRhythm", "companionshipDistance"}),
        (
            "我能接受规律梳毛和中等花费，没有绝对不能接受的日常负担。",
            {"ongoingInvestmentWillingness", "disturbanceTolerance", "absoluteBottomLines"},
        ),
        ("猫狗都不过敏。", {"allergySpecies"}),
    )

    for index, (text, expected_slots) in enumerate(turns, start=1):
        message_id = f"message-{index}"
        response = provider.extract_profile(
            ProfileExtractionRequest(
                scenarioId="browser-demo",
                stepId=f"turn-{index}:extract",
                messageId=message_id,
                text=text,
            )
        )
        assert response.delta.sourceMessageId == message_id
        assert {change.slotName for change in response.delta.changes} == expected_slots


def test_demo_provider_keeps_deterministic_question_selection_unchanged() -> None:
    request = QuestionWordingRequest(
        scenarioId="browser-demo",
        stepId="turn-1:question",
        questionId="ask-current-time",
        prompt="普通工作日里，你大概能留出多少时间陪它？",
        quickReplies=("比较有限", "能安排一些", "比较充足"),
    )

    response = DemoMockProvider().phrase_question(request)

    assert response.questionId == request.questionId
    assert response.quickReplies == request.quickReplies
    assert response.text == request.prompt


def test_demo_provider_returns_an_empty_safe_delta_for_unrecognised_text() -> None:
    response = DemoMockProvider().extract_profile(
        ProfileExtractionRequest(
            scenarioId="browser-demo",
            stepId="turn-unknown:extract",
            messageId="message-unknown",
            text="我还没想好。",
        )
    )

    assert response.delta == ProfileDelta(
        sourceMessageId="message-unknown",
        changes=(),
    )
