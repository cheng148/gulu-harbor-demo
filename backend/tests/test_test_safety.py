import pytest

from app.core.config import assert_test_model_is_safe


def test_automated_tests_allow_the_mock_provider() -> None:
    assert_test_model_is_safe("mock")


def test_automated_tests_reject_the_deepseek_provider() -> None:
    with pytest.raises(RuntimeError, match="MODEL_PROVIDER=mock"):
        assert_test_model_is_safe("deepseek")
