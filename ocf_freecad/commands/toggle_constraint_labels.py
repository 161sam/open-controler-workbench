from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class ToggleConstraintLabelsCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Toggle Constraint Labels",
            "ToolTip": "Show or hide textual labels for constraint feedback",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="layout").toggle_constraint_labels()
