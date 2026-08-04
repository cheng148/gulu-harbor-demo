def assert_test_model_is_safe(provider: str) -> None:
    """阻止自动化测试意外调用真实模型。"""
    if provider.strip().lower() != "mock":
        raise RuntimeError(
            "Automated tests require MODEL_PROVIDER=mock; real model calls are disabled."
        )
