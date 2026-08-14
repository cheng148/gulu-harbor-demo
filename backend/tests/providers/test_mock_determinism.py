from __future__ import annotations

import socket

import pytest

from app.providers.base import ProviderFailure, ProviderFailureCode

from .test_provider_contract import provider


def test_same_fixture_and_input_are_byte_stable_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Mock provider must not access the network")

    monkeypatch.setattr(socket, "socket", reject_network)
    first = provider()
    second = provider()
    request = first.fixtures.profileExtractions[0].request

    first_json = first.extract_profile(request).model_dump_json()
    second_json = second.extract_profile(request).model_dump_json()

    assert first_json.encode() == second_json.encode()


def test_mock_does_not_read_deepseek_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_environment_read(key: str, default: str | None = None) -> str | None:
        if key.startswith("DEEPSEEK"):
            raise AssertionError("Mock provider must not read DeepSeek configuration")
        return default

    monkeypatch.setattr("os.getenv", reject_environment_read)
    mock = provider()

    mock.phrase_question(mock.fixtures.questionWordings[0].request)


def test_unregistered_input_fails_instead_of_inventing_an_answer() -> None:
    mock = provider()
    request = mock.fixtures.profileExtractions[0].request.model_copy(
        update={"text": "这是夹具里没有的新输入"}
    )

    with pytest.raises(ProviderFailure) as error:
        mock.extract_profile(request)

    assert error.value.code is ProviderFailureCode.NO_FIXTURE
