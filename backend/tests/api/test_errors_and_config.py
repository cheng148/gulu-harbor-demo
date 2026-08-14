from collections.abc import Callable

import pytest
from fastapi import Query
from fastapi.testclient import TestClient

from app.api.errors import PublicAPIError
from app.core.config import (
    AppSettings,
    ConfigurationError,
    ModelProvider,
    load_settings,
)
from app.main import create_app
from app.providers.deepseek import DeepSeekProvider


def _client_with_route(
    route: Callable[[], None], *, raise_server_exceptions: bool = True
) -> TestClient:
    app = create_app(settings=AppSettings(modelProvider=ModelProvider.MOCK))
    app.get("/_test/error")(route)
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_mock_mode_starts_without_a_deepseek_key() -> None:
    settings = load_settings({"MODEL_PROVIDER": "mock", "DEEPSEEK_API_KEY": ""})

    response = TestClient(create_app(settings=settings)).get("/health")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "status": "ok",
        "service": "gulu-port-agent",
        "dependencies": {"configuration": "ok"},
    }


@pytest.mark.parametrize("api_key", [None, "", "   "])
def test_deepseek_mode_fails_startup_without_a_key(api_key: str | None) -> None:
    environment = {"MODEL_PROVIDER": "deepseek"}
    if api_key is not None:
        environment["DEEPSEEK_API_KEY"] = api_key

    with pytest.raises(ConfigurationError, match="DEEPSEEK_API_KEY"):
        load_settings(environment)


def test_unsupported_provider_fails_with_a_clear_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="MODEL_PROVIDER"):
        load_settings({"MODEL_PROVIDER": "unknown"})


def test_deepseek_settings_are_configurable_without_exposing_the_key() -> None:
    settings = load_settings(
        {
            "MODEL_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "test-key",
            "DEEPSEEK_BASE_URL": "https://example.test/deepseek/",
            "DEEPSEEK_MODEL": "demo-model",
            "DEEPSEEK_TIMEOUT_SECONDS": "17.5",
        }
    )

    assert settings.deepseekBaseUrl == "https://example.test/deepseek"
    assert settings.deepseekModel == "demo-model"
    assert settings.deepseekTimeoutSeconds == 17.5
    assert settings.deepseekApiKey is not None
    assert settings.deepseekApiKey.get_secret_value() == "test-key"
    assert "test-key" not in repr(settings)


def test_deepseek_settings_have_safe_demo_defaults() -> None:
    settings = load_settings(
        {"MODEL_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "test-key"}
    )

    assert settings.deepseekBaseUrl == "https://api.deepseek.com"
    assert settings.deepseekModel == "deepseek-v4-flash"
    assert settings.deepseekTimeoutSeconds == 30.0


def test_deepseek_mode_builds_the_real_provider_without_calling_the_network() -> None:
    settings = load_settings(
        {"MODEL_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "test-key"}
    )

    app = create_app(settings=settings)

    assert isinstance(app.state.model_provider, DeepSeekProvider)


@pytest.mark.parametrize("timeout", ["0", "-1", "not-a-number"])
def test_invalid_deepseek_timeout_fails_configuration(timeout: str) -> None:
    with pytest.raises(ConfigurationError, match="DEEPSEEK_TIMEOUT_SECONDS"):
        load_settings(
            {
                "MODEL_PROVIDER": "deepseek",
                "DEEPSEEK_API_KEY": "test-key",
                "DEEPSEEK_TIMEOUT_SECONDS": timeout,
            }
        )


def test_deepseek_base_url_requires_encrypted_https() -> None:
    with pytest.raises(ConfigurationError, match="DEEPSEEK_BASE_URL"):
        load_settings(
            {
                "MODEL_PROVIDER": "deepseek",
                "DEEPSEEK_API_KEY": "test-key",
                "DEEPSEEK_BASE_URL": "http://api.deepseek.test",
            }
        )


def test_health_response_has_a_request_id_and_no_sensitive_configuration() -> None:
    settings = load_settings(
        {
            "MODEL_PROVIDER": "deepseek",
            "DEEPSEEK_API_KEY": "super-secret-test-key",
            "DEEPSEEK_MODEL": "private-model-name",
            "DATABASE_PATH": "C:/private/database.sqlite",
        }
    )

    response = TestClient(create_app(settings=settings)).get("/health")

    body = response.json()
    assert response.status_code == 200
    assert isinstance(body["meta"]["requestId"], str)
    assert body["meta"]["requestId"]
    serialized = response.text
    assert "super-secret-test-key" not in serialized
    assert "private-model-name" not in serialized
    assert "C:/private" not in serialized
    assert "deepseek" not in serialized.lower()


def test_expected_api_error_uses_the_common_error_contract() -> None:
    def route() -> None:
        raise PublicAPIError(
            status_code=409,
            code="REVISION_CONFLICT",
            message="页面内容已更新，请刷新后再试。",
            retryable=True,
            details={"currentRevision": 4},
        )

    response = _client_with_route(route).get("/_test/error")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "REVISION_CONFLICT",
            "message": "页面内容已更新，请刷新后再试。",
            "retryable": True,
            "details": {"currentRevision": 4},
        },
        "meta": {"requestId": response.json()["meta"]["requestId"]},
    }


def test_validation_error_uses_the_common_error_contract() -> None:
    app = create_app(settings=AppSettings(modelProvider=ModelProvider.MOCK))

    @app.get("/_test/validation")
    def validation_route(limit: int = Query(ge=1, le=10)) -> dict[str, int]:
        return {"limit": limit}

    response = TestClient(app).get("/_test/validation", params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["retryable"] is False
    assert response.json()["error"]["details"]


def test_unexpected_error_does_not_expose_internal_details() -> None:
    def route() -> None:
        raise RuntimeError("secret stack detail C:/private/app.py")

    response = _client_with_route(route, raise_server_exceptions=False).get(
        "/_test/error"
    )

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "INTERNAL_ERROR",
        "message": "服务暂时遇到问题，请稍后再试。",
        "retryable": True,
        "details": {},
    }
    assert "secret stack detail" not in response.text
    assert "C:/private" not in response.text
