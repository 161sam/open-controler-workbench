from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_EVENT_TYPES = ("SoMouseButtonEvent", "SoLocation2Event", "SoKeyboardEvent")


class ViewEventCallbackRegistry:
    def __init__(self, event_types: tuple[str, ...] = DEFAULT_EVENT_TYPES) -> None:
        self.event_types = tuple(event_types)
        self.view: Any | None = None
        self._handles: list[tuple[str, Any]] = []
        self._callback: Any | None = None

    @property
    def is_registered(self) -> bool:
        return bool(self._handles)

    def attach(self, view: Any, callback: Any) -> bool:
        if view is None or not hasattr(view, "addEventCallback"):
            self.detach()
            return False
        if self.view is view and self._callback is callback and self._handles:
            return True
        self.detach()
        handles: list[tuple[str, Any]] = []
        for event_type in self.event_types:
            try:
                handle = view.addEventCallback(event_type, callback)
            except Exception:
                continue
            handles.append((event_type, handle))
        if not handles:
            try:
                handle = view.addEventCallback("SoEvent", callback)
            except Exception:
                self.view = None
                self._callback = None
                self._handles = []
                return False
            handles.append(("SoEvent", handle))
        self.view = view
        self._callback = callback
        self._handles = handles
        return True

    def detach(self) -> None:
        view = self.view
        handles = list(self._handles)
        self.view = None
        self._callback = None
        self._handles = []
        if view is None or not hasattr(view, "removeEventCallback"):
            return
        for event_type, handle in handles:
            try:
                view.removeEventCallback(event_type, handle)
            except Exception:
                continue


@dataclass
class ActiveInteractionSession:
    name: str
    doc: Any
    cancel: Callable[[str, bool], None]


class InteractionSessionManager:
    def __init__(self) -> None:
        self._active: ActiveInteractionSession | None = None

    @property
    def active_name(self) -> str | None:
        return None if self._active is None else self._active.name

    def activate(self, name: str, doc: Any, cancel: Callable[[str, bool], None]) -> None:
        if self._active is not None:
            self._active.cancel("switch", False)
        self._active = ActiveInteractionSession(name=name, doc=doc, cancel=cancel)

    def clear(self, cancel: Callable[[str, bool], None]) -> None:
        if self._active is not None and self._active.cancel == cancel:
            self._active = None

    def cancel_active(self, reason: str = "cancel", publish_status: bool = True) -> None:
        active = self._active
        if active is None:
            return
        self._active = None
        active.cancel(reason, publish_status)

    def handle_document_changed(self, doc: Any | None) -> None:
        active = self._active
        if active is None:
            return
        if active.doc is doc:
            return
        self.cancel_active(reason="document_changed", publish_status=False)

    def handle_document_closed(self, doc: Any) -> None:
        active = self._active
        if active is None:
            return
        if active.doc is doc:
            self.cancel_active(reason="document_closed", publish_status=False)
