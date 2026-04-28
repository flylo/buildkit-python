from importlib import import_module


def test_package_is_importable() -> None:
    module = import_module("zeroshot_commons_testing")
    assert module is not None
