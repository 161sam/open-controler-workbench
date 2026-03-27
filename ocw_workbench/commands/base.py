from __future__ import annotations

from ocw_workbench.gui.runtime import icon_path


class BaseCommand:
    ICON_NAME = "default"

    def icon_name(self) -> str:
        return self.ICON_NAME

    def resources(self, menu_text: str, tooltip: str, accel: str | None = None) -> dict[str, str]:
        payload = {
            "MenuText": menu_text,
            "ToolTip": tooltip,
            "Pixmap": icon_path(self.icon_name()),
        }
        if accel:
            payload["Accel"] = accel
        return payload

    def GetResources(self):
        return self.resources("Base Command", "Base Command")

    def IsActive(self):
        return True
