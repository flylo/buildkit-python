from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock, Timer


AbortListener = Callable[[], None]


@dataclass
class AbortSignal:
    aborted: bool = False
    _listeners: list[AbortListener] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def add_event_listener(self, event_name: str, listener: AbortListener) -> None:
        if event_name != "abort":
            return
        with self._lock:
            self._listeners.append(listener)

    def remove_event_listener(self, event_name: str, listener: AbortListener) -> None:
        if event_name != "abort":
            return
        with self._lock:
            self._listeners = [existing for existing in self._listeners if existing is not listener]

    def _fire_abort(self) -> None:
        with self._lock:
            if self.aborted:
                return
            self.aborted = True
            listeners = list(self._listeners)

        for listener in listeners:
            listener()


class TimeoutAbortController:
    def __init__(self) -> None:
        self._signal = AbortSignal()
        self._timeout: Timer | None = None
        self._lock = Lock()
        self._abort_listener: AbortListener | None = self.clear_timeout
        self._signal.add_event_listener("abort", self._abort_listener)

    def set_timeout(self, timeout_ms: int) -> AbortSignal:
        self.clear_timeout()
        timer = Timer(timeout_ms / 1000, self.abort)
        timer.daemon = True
        with self._lock:
            self._timeout = timer
        timer.start()
        return self._signal

    def clear_timeout(self) -> None:
        with self._lock:
            timer = self._timeout
            self._timeout = None
        if timer is not None:
            timer.cancel()

    @property
    def signal(self) -> AbortSignal:
        return self._signal

    def abort(self) -> None:
        self._signal._fire_abort()

    def dispose(self) -> None:
        self.clear_timeout()
        if self._abort_listener is not None:
            self._signal.remove_event_listener("abort", self._abort_listener)
            self._abort_listener = None

    @classmethod
    def with_timeout(cls, timeout_ms: int) -> tuple["TimeoutAbortController", AbortSignal]:
        controller = cls()
        signal = controller.set_timeout(timeout_ms)
        return controller, signal
