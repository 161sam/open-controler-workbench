from __future__ import annotations

from dataclasses import dataclass

from ocw_workbench.commands.base import BaseCommand
from ocw_workbench.commands.factory import (
    PluginCommandSpec,
    component_toolbar_command_ids as _factory_component_toolbar_command_ids,
    component_toolbar_groups as _factory_component_toolbar_groups,
    iter_plugin_command_specs,
    plugin_command_specs_by_component,
)
from ocw_workbench.gui.interaction.placement_controller import PlacementController
from ocw_workbench.gui.runtime import component_icon_path, show_error, show_info
from ocw_workbench.services.controller_service import ControllerService
from ocw_workbench.services.interaction_service import InteractionService


@dataclass(frozen=True)
class ComponentTypeCommandSpec:
    component_type: str
    label: str
    icon_filename: str
    default_library_ref: str
    category: str = "Components"
    plugin_id: str = "midicontroller"

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
    def toolbar_name(self) -> str:
        return f"OCW {self.category}"

    @property
    def dialog_title(self) -> str:
        return f"Place {self.label}"

    @property
    def start_message(self) -> str:
        return f"Click in the 3D view to place a {self.label}. Press ESC to cancel."


def _fallback_specs() -> tuple[ComponentTypeCommandSpec, ...]:
    return (
        ComponentTypeCommandSpec("button", "Button", "button.svg", "omron_b3f_1000", category="Buttons"),
        ComponentTypeCommandSpec("encoder", "Encoder", "encoder.svg", "alps_ec11e15204a3", category="Encoders"),
        ComponentTypeCommandSpec("fader", "Fader", "fader.svg", "generic_45mm_linear_fader", category="Faders"),
        ComponentTypeCommandSpec("pad", "Pad", "pad.svg", "generic_mpc_pad_30mm", category="Pads"),
        ComponentTypeCommandSpec("display", "Display", "display.svg", "adafruit_oled_096_i2c_ssd1306", category="Displays"),
        ComponentTypeCommandSpec("rgb_button", "RGB Button", "generic.svg", "generic_rgb_arcade_button_24mm", category="Buttons"),
    )


def _plugin_specs() -> tuple[ComponentTypeCommandSpec, ...]:
    specs: list[ComponentTypeCommandSpec] = []
    for spec in iter_plugin_command_specs():
        if spec.command_type != "place_component" or spec.component is None or spec.library_ref is None:
            continue
        specs.append(
            ComponentTypeCommandSpec(
                component_type=spec.component,
                label=spec.label.replace("Place ", "", 1),
                icon_filename=spec.icon,
                default_library_ref=spec.library_ref,
                category=spec.category,
                plugin_id=spec.plugin_id or "midicontroller",
            )
        )
    return tuple(specs)


def _active_specs() -> tuple[ComponentTypeCommandSpec, ...]:
    plugin_specs = _plugin_specs()
    return plugin_specs if plugin_specs else _fallback_specs()


_TYPE_SPECS: tuple[ComponentTypeCommandSpec, ...] = _active_specs()
_TYPE_SPEC_BY_NAME = {spec.component_type: spec for spec in _TYPE_SPECS}

_TYPE_DEFAULTS: dict[str, str] = {spec.component_type: spec.default_library_ref for spec in _TYPE_SPECS}
_TYPE_ICONS: dict[str, str] = {spec.component_type: spec.icon_filename for spec in _TYPE_SPECS}
_TYPE_LABELS: dict[str, str] = {spec.component_type: spec.label for spec in _TYPE_SPECS}


def iter_component_type_command_specs() -> tuple[ComponentTypeCommandSpec, ...]:
    return _active_specs()


def component_toolbar_command_ids() -> list[str]:
    factory_ids = _factory_component_toolbar_command_ids()
    if factory_ids:
        return factory_ids
    return [spec.command_id for spec in _active_specs()]


def component_toolbar_groups(active_plugin_id: str | None = None) -> list[tuple[str, list[str]]]:
    factory_groups = _factory_component_toolbar_groups(active_plugin_id=active_plugin_id)
    if factory_groups:
        return factory_groups
    relevant_specs = [spec for spec in _active_specs() if active_plugin_id in {None, "", spec.plugin_id}]
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for spec in relevant_specs:
        toolbar_name = spec.toolbar_name
        if toolbar_name not in grouped:
            grouped[toolbar_name] = []
            order.append(toolbar_name)
        grouped[toolbar_name].append(spec.command_id)
    return [(toolbar_name, grouped[toolbar_name]) for toolbar_name in order]


class PlaceComponentTypeCommand(BaseCommand):
    """Start direct 3D placement for a component type using its default library variant."""

    def __init__(self, component_type: str, spec: PluginCommandSpec | None = None) -> None:
        self.component_type = component_type
        if spec is not None:
            self.spec = ComponentTypeCommandSpec(
                component_type=component_type,
                label=spec.label.replace("Place ", "", 1),
                icon_filename=spec.icon,
                default_library_ref=spec.library_ref or component_type,
                category=spec.category,
                plugin_id=spec.plugin_id or "midicontroller",
            )
        else:
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
            "Category": self.spec.category,
        }

    def IsActive(self) -> bool:
        return self._has_controller()

    def Activated(self) -> None:
        try:
            import FreeCAD as App

            doc = App.ActiveDocument
            if doc is None:
                raise RuntimeError("No active FreeCAD document")

            interaction_service = InteractionService(ControllerService())
            interaction_service.set_active_component_template(doc, self.default_library_ref)
            started = PlacementController().start_component_placement(doc, self.default_library_ref)
            if not started:
                raise RuntimeError("Could not start 3D placement mode")

            show_info(self.spec.dialog_title, self.spec.start_message)
        except Exception as exc:
            show_error(self.spec.dialog_title, exc)
