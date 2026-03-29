from __future__ import annotations

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import show_error, show_info


class ReloadPluginsCommand(BaseCommand):
    ICON_NAME = "plugin_reload"

    def GetResources(self):
        return self.resources(
            "Reload Plugins",
            "Reload plugin packs and refresh status.",
        )

    def Activated(self):
        try:
            import FreeCAD as App

            from ocw_workbench.workbench import reload_plugins_direct

            doc = App.ActiveDocument or App.newDocument("Controller")
            result = reload_plugins_direct(doc)
            show_info("Reload Plugins", f"Discovered {len(result)} plugins.")
        except Exception as exc:
            show_error("Reload Plugins", exc)
