from importlib import import_module


def test_package_is_importable() -> None:
    module = import_module("zeroshot_agent_experiments")
    assert module is not None
