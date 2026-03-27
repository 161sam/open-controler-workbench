from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand


class ValidateLayoutCommand(BaseCommand):
    ICON_NAME = "validate_constraints"

    def GetResources(self):
        return self.resources("Validate Layout", "Show constraint validation results")

    def Activated(self):
        import FreeCAD as App
        import FreeCADGui as Gui

        from ocw_workbench.gui.taskpanels.constraints_taskpanel import ConstraintsTaskPanel

        doc = App.ActiveDocument
        if doc is None:
            raise RuntimeError("No active FreeCAD document")
        Gui.Control.showDialog(ConstraintsTaskPanel(doc))
