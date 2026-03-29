from __future__ import annotations

import importlib

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.panels._common import log_to_console
from ocw_workbench.gui.runtime import show_error, show_info


class ValidateConstraintsCommand(BaseCommand):
    ICON_NAME = "validate_constraints"

    def GetResources(self):
        return self.resources(
            "Validate Layout",
            "Check spacing, edge distance, and placement rules.",
        )

    def IsActive(self):
        return self._has_controller()

    def Activated(self):
        try:
            import FreeCAD as App
            from ocw_workbench.services.controller_service import ControllerService
            workbench_module = importlib.import_module("ocw_workbench.workbench")

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")

            cs = ControllerService()
            report = cs.validate_layout(doc)
            ensure_overlay_visible = getattr(workbench_module, "ensure_constraint_overlay_visible_direct", None)
            if callable(ensure_overlay_visible):
                ensure_overlay_visible(doc, True)
            refresh_workbench = getattr(workbench_module, "_refresh_active_workbench_if_open", None)
            if callable(refresh_workbench):
                refresh_workbench(doc)

            summary = report.get("summary", {})
            error_count = summary.get("error_count", 0)
            warning_count = summary.get("warning_count", 0)
            log_to_console(
                f"Constraint validation finished with {error_count} errors and {warning_count} warnings."
            )
            if error_count == 0 and warning_count == 0:
                show_info("Validate Layout", "No issues found. Constraint overlay remains visible for direct inspection.")
            else:
                show_info(
                    "Validate Layout",
                    f"{error_count} error(s), {warning_count} warning(s). Issues are visible directly in the 3D overlay.",
                )
        except Exception as exc:
            show_error("Validate Constraints", exc)
