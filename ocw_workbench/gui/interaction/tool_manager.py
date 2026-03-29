from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ActiveTool:
    tool_id: str
    deactivate: Callable[[], None] | None = None
    context: Any | None = None


class ToolManager:
    def __init__(self) -> None:
        self._active: ActiveTool | None = None

    @property
    def current_tool(self) -> str | None:
        return None if self._active is None else self._active.tool_id

    def activate_tool(
        self,
        tool_id: str,
        *,
        activator: Callable[[], bool],
        deactivate: Callable[[], None] | None = None,
        context: Any | None = None,
    ) -> bool:
        if self._active is not None and self._active.deactivate is not None:
            self._active.deactivate()
        started = bool(activator())
        if not started:
            self._active = None
            return False
        self._active = ActiveTool(tool_id=tool_id, deactivate=deactivate, context=context)
        return True

    def deactivate_tool(self) -> None:
        if self._active is None:
            return
        active = self._active
        self._active = None
        if active.deactivate is not None:
            active.deactivate()

    def clear_active_tool(self, tool_id: str | None = None) -> None:
        if self._active is None:
            return
        if tool_id not in {None, self._active.tool_id}:
            return
        self._active = None


_TOOL_MANAGER = ToolManager()


def get_tool_manager() -> ToolManager:
    return _TOOL_MANAGER


def reset_tool_manager() -> ToolManager:
    global _TOOL_MANAGER
    _TOOL_MANAGER = ToolManager()
    return _TOOL_MANAGER
