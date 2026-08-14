from __future__ import annotations

import os
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class ConfigurationError(RuntimeError):
    """Raised when the service cannot start safely with its configuration."""


class ModelProvider(StrEnum):
    MOCK = "mock"
    DEEPSEEK = "deepseek"


class AppSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    modelProvider: ModelProvider = ModelProvider.MOCK
    deepseekApiKey: SecretStr | None = None
    deepseekBaseUrl: str = "https://api.deepseek.com"
    deepseekModel: str = "deepseek-v4-flash"
    deepseekTimeoutSeconds: float = Field(default=30.0, gt=0, le=120)

    def validate_for_startup(self) -> None:
        if self.modelProvider is ModelProvider.DEEPSEEK:
            key = self.deepseekApiKey
            if key is None or not key.get_secret_value().strip():
                raise ConfigurationError(
                    "DEEPSEEK_API_KEY is required when MODEL_PROVIDER=deepseek."
                )


def load_settings(environ: Mapping[str, str] | None = None) -> AppSettings:
    source = os.environ if environ is None else environ
    raw_provider = source.get("MODEL_PROVIDER", ModelProvider.MOCK.value)
    try:
        provider = ModelProvider(raw_provider.strip().lower())
    except ValueError as error:
        allowed = ", ".join(item.value for item in ModelProvider)
        raise ConfigurationError(
            f"MODEL_PROVIDER must be one of: {allowed}."
        ) from error

    if provider is ModelProvider.MOCK:
        settings = AppSettings(modelProvider=provider)
    else:
        raw_key = source.get("DEEPSEEK_API_KEY")
        raw_base_url = source.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        base_url = raw_base_url.strip().rstrip("/")
        model = source.get("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()
        raw_timeout = source.get("DEEPSEEK_TIMEOUT_SECONDS", "30")
        try:
            timeout_seconds = float(raw_timeout)
            settings = AppSettings(
                modelProvider=provider,
                deepseekApiKey=SecretStr(raw_key) if raw_key is not None else None,
                deepseekBaseUrl=base_url,
                deepseekModel=model,
                deepseekTimeoutSeconds=timeout_seconds,
            )
        except (TypeError, ValueError) as error:
            raise ConfigurationError(
                "DEEPSEEK_TIMEOUT_SECONDS must be greater than 0 and at most 120."
            ) from error
        if not base_url.startswith("https://"):
            raise ConfigurationError("DEEPSEEK_BASE_URL must be an HTTPS URL.")
        if not model:
            raise ConfigurationError("DEEPSEEK_MODEL must not be empty.")
    settings.validate_for_startup()
    return settings


def assert_test_model_is_safe(provider: str) -> None:
    """阻止自动化测试意外调用真实模型。"""
    if provider.strip().lower() != ModelProvider.MOCK.value:
        raise RuntimeError(
            "Automated tests require MODEL_PROVIDER=mock; real model calls are disabled."
        )
