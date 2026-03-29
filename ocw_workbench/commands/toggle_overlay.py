from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class ToggleOverlayCommand(BaseCommand):
    ICON_NAME = "toggle_overlay"

    def GetResources(self):
        return self.resources(
            "Overlay",
            "Show or hide layout guides.",
        )

    def IsActive(self):
        return self._has_controller()

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import toggle_overlay_direct

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            settings = toggle_overlay_direct(doc)
            show_info(
                "Overlay",
                f"Overlay {'enabled' if settings['overlay_enabled'] else 'disabled'}.",
            )
        except Exception as exc:
            show_error("Toggle Overlay", exc)
