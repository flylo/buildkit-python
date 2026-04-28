from __future__ import annotations

from time import sleep

from zeroshot_commons import TimeoutAbortController


def test_timeout_abort_controller_lifecycle() -> None:
    controller = TimeoutAbortController()
    signal = controller.set_timeout(10)
    events: list[str] = []
    signal.add_event_listener("abort", lambda: events.append("abort"))

    sleep(0.03)

    assert signal.aborted is True
    assert events == ["abort"]
    controller.dispose()


def test_timeout_abort_controller_clear_timeout_prevents_abort() -> None:
    controller = TimeoutAbortController()
    signal = controller.set_timeout(50)
    controller.clear_timeout()

    sleep(0.07)

    assert signal.aborted is False
    controller.dispose()


def test_timeout_abort_controller_with_timeout_returns_controller_and_signal() -> None:
    controller, signal = TimeoutAbortController.with_timeout(5)
    sleep(0.02)
    assert signal.aborted is True
    controller.dispose()
