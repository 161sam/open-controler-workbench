from __future__ import annotations

import importlib
from typing import Any

from ocw_workbench.gui.interaction.tool_manager import get_tool_manager


class PlacementController:
    """Start direct-manipulation placement and move tools without requiring the dock."""

    def start_component_placement(self, doc: Any, template_id: str) -> bool:
        workbench_module = importlib.import_module("ocw_workbench.workbench")
        start_place_mode_direct = getattr(workbench_module, "start_place_mode_direct")
        cancel_active_tool = getattr(workbench_module, "cancel_active_tool", lambda current_doc=None: None)

        tool_id = f"place:{template_id}"
        return get_tool_manager().activate_tool(
            tool_id,
            activator=lambda: bool(start_place_mode_direct(doc, template_id)),
            deactivate=lambda: cancel_active_tool(doc),
            context={"doc": doc, "template_id": template_id},
        )

    def start_move_mode(self, doc: Any) -> bool:
        workbench_module = importlib.import_module("ocw_workbench.workbench")
        start_component_drag_mode_direct = getattr(workbench_module, "start_component_drag_mode_direct")
        cancel_active_tool = getattr(workbench_module, "cancel_active_tool", lambda current_doc=None: None)

        return get_tool_manager().activate_tool(
            "drag",
            activator=lambda: bool(start_component_drag_mode_direct(doc)),
            deactivate=lambda: cancel_active_tool(doc),
            context={"doc": doc},
        )
