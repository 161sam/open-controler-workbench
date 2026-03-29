from __future__ import annotations

from dataclasses import dataclass

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.gui.runtime import component_icon_path, show_error, show_info
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.interaction_service import InteractionService


@dataclass(frozen=True)
class ComponentTypeCommandSpec:
    component_type: str
    label: str
    icon_filename: str
    default_library_ref: str

    @property
    def command_id(self) -> str:
        suffix = self.component_type.replace("_", " ").title().replace(" ", "")
        return f"OCW_Place{suffix}"

    @property
    def menu_text(self) -> str:
        return f"Place {self.label}"

    @property
    def tooltip(self) -> str:
        return f"Start 3D placement for a {self.label}. Click in the 3D view to position it."

    @property
    def dialog_title(self) -> str:
        return f"Place {self.label}"

    @property
    def start_message(self) -> str:
        return f"Click in the 3D view to place a {self.label}. Press ESC to cancel."


_TYPE_SPECS: tuple[ComponentTypeCommandSpec, ...] = (
    ComponentTypeCommandSpec("button", "Button", "button.svg", "omron_b3f_1000"),
    ComponentTypeCommandSpec("encoder", "Encoder", "encoder.svg", "alps_ec11e15204a3"),
    ComponentTypeCommandSpec("fader", "Fader", "fader.svg", "generic_45mm_linear_fader"),
    ComponentTypeCommandSpec("pad", "Pad", "pad.svg", "generic_mpc_pad_30mm"),
    ComponentTypeCommandSpec("display", "Display", "display.svg", "adafruit_oled_096_i2c_ssd1306"),
    ComponentTypeCommandSpec("rgb_button", "RGB Button", "generic.svg", "generic_rgb_arcade_button_24mm"),
)
_TYPE_SPEC_BY_NAME = {spec.component_type: spec for spec in _TYPE_SPECS}

_TYPE_DEFAULTS: dict[str, str] = {spec.component_type: spec.default_library_ref for spec in _TYPE_SPECS}
_TYPE_ICONS: dict[str, str] = {spec.component_type: spec.icon_filename for spec in _TYPE_SPECS}
_TYPE_LABELS: dict[str, str] = {spec.component_type: spec.label for spec in _TYPE_SPECS}


def iter_component_type_command_specs() -> tuple[ComponentTypeCommandSpec, ...]:
    return _TYPE_SPECS


def component_toolbar_command_ids() -> list[str]:
    return [spec.command_id for spec in _TYPE_SPECS]


class PlaceComponentTypeCommand(BaseCommand):
    """Start direct 3D placement for a component type using its default library variant."""

    def __init__(self, component_type: str) -> None:
        self.component_type = component_type
        self.spec = _TYPE_SPEC_BY_NAME.get(
            component_type,
            ComponentTypeCommandSpec(
                component_type=component_type,
                label=component_type.replace("_", " ").title(),
                icon_filename="generic.svg",
                default_library_ref=component_type,
            ),
        )
        self.default_library_ref = self.spec.default_library_ref

    def icon_name(self) -> str:
        return ""

    def GetResources(self) -> dict:
        return {
            "MenuText": self.spec.menu_text,
            "ToolTip": self.spec.tooltip,
            "Pixmap": component_icon_path(self.spec.icon_filename),
        }

    def IsActive(self) -> bool:
        return self._has_controller()

    def Activated(self) -> None:
        try:
            import FreeCAD as App
            from ocw_workbench.workbench import start_place_mode_direct

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")

            interaction_service = InteractionService(ControllerService())
            interaction_service.set_active_component_template(doc, self.default_library_ref)
            started = start_place_mode_direct(doc, self.default_library_ref)
            if not started:
                raise RuntimeError("Could not start 3D placement mode")

            show_info(self.spec.dialog_title, self.spec.start_message)
        except Exception as exc:
            show_error(self.spec.dialog_title, exc)
