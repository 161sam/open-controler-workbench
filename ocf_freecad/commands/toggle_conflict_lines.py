from __future__ import annotations

from ocf_freecad.commands.base import BaseCommand


class ToggleConflictLinesCommand(BaseCommand):
    def GetResources(self):
        return {
            "MenuText": "Toggle Conflict Lines",
            "ToolTip": "Show or hide conflict connection lines in the constraint overlay",
        }

    def Activated(self):
        import FreeCAD as App

        from ocf_freecad.workbench import ensure_workbench_ui

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        ensure_workbench_ui(doc, focus="layout").toggle_conflict_lines()
