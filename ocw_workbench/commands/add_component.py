from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.panels._common import log_to_console
from ocw_workbench.gui.runtime import show_error, show_info
from ocw_workbench.services.interaction_service import InteractionService


class AddComponentCommand(BaseCommand):
    ICON_NAME = "add_component"

    def GetResources(self):
        return self.resources(
            "Add Component",
            "Add a component to the current controller.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.services.controller_service import ControllerService
            from ocw_workbench.workbench import ensure_component_palette_ui, start_place_mode_direct

            doc = App.ActiveDocument or App.newDocument("Controller")
            controller_service = ControllerService()
            settings = InteractionService(controller_service).get_settings(doc)
            template_id = settings.get("active_component_template_id")
            if isinstance(template_id, str) and template_id:
                started = start_place_mode_direct(doc, template_id)
                if started:
                    show_info("Add Component", f"Click to place '{template_id}' in the 3D view. Press ESC to cancel.")
                    log_to_console(f"Add Component command started place mode for '{template_id}'.")
                    return
            ensure_component_palette_ui(doc)
            show_info("Add Component", "Select a component template, then click in the 3D view to place it.")
            log_to_console("Add Component command focused the palette because no active template was set.")
        except Exception as exc:
            show_error("Add Component", exc)
