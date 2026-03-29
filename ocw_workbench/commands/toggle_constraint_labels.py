from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class ToggleConstraintLabelsCommand(BaseCommand):
    ICON_NAME = "constraint_labels"

    def GetResources(self):
        return self.resources(
            "Issue Labels",
            "Show or hide issue labels in the 3D view.",
        )

    def IsActive(self):
        return self._has_controller()

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import toggle_constraint_labels_direct

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")
            settings = toggle_constraint_labels_direct(doc)
            show_info(
                "Constraint Labels",
                f"Constraint labels {'enabled' if settings['constraint_labels_enabled'] else 'disabled'}.",
            )
        except Exception as exc:
            show_error("Toggle Constraint Labels", exc)
