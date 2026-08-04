import os

import pytest

from app.core.config import assert_test_model_is_safe


def pytest_sessionstart(session: pytest.Session) -> None:
    del session
    configured_provider = os.getenv("MODEL_PROVIDER", "mock")
    try:
        assert_test_model_is_safe(configured_provider)
    except RuntimeError as error:
        raise pytest.UsageError(str(error)) from error

    os.environ["MODEL_PROVIDER"] = "mock"
