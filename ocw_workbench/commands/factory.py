from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ocw_workbench.services.plugin_service import get_plugin_service


@dataclass(frozen=True)
class PluginCommandSpec:
    id: str
    command_id: str
    command_type: str
    label: str
    tooltip: str
    icon: str
    category: str
    component: str | None = None
    library_ref: str | None = None
    plugin_id: str | None = None

    @property
    def menu_text(self) -> str:
        return self.label

    @property
    def dialog_title(self) -> str:
        return self.label

    @property
    def start_message(self) -> str:
        noun = self.label.replace("Place ", "", 1)
        return f"Click in the 3D view to place a {noun}. Press ESC to cancel."

    @property
    def toolbar_name(self) -> str:
        return f"OCW {self.category}"


def iter_plugin_command_specs(active_plugin_only: bool = True) -> tuple[PluginCommandSpec, ...]:
    commands = _command_metadata(active_plugin_only=active_plugin_only)
    specs: list[PluginCommandSpec] = []
    for command_id, metadata in commands.items():
        if not isinstance(metadata, dict):
            continue
        specs.append(_build_spec(command_id, metadata))
    return tuple(specs)


def plugin_command_specs_by_component(active_plugin_only: bool = True) -> dict[str, PluginCommandSpec]:
    return {
        spec.component: spec
        for spec in iter_plugin_command_specs(active_plugin_only=active_plugin_only)
        if spec.component is not None
    }


def component_toolbar_command_ids() -> list[str]:
    return [spec.command_id for spec in iter_plugin_command_specs() if spec.command_type == "place_component"]


def component_toolbar_groups(active_plugin_id: str | None = None) -> list[tuple[str, list[str]]]:
    grouped: dict[str, list[str]] = {}
    order: list[str] = []
    for spec in iter_plugin_command_specs():
        if spec.command_type != "place_component":
            continue
        if active_plugin_id not in {None, "", spec.plugin_id}:
            continue
        if spec.toolbar_name not in grouped:
            grouped[spec.toolbar_name] = []
            order.append(spec.toolbar_name)
        grouped[spec.toolbar_name].append(spec.command_id)
    return [(toolbar_name, grouped[toolbar_name]) for toolbar_name in order]


def command_specs_by_command_id() -> dict[str, PluginCommandSpec]:
    return {spec.command_id: spec for spec in iter_plugin_command_specs()}


def build_plugin_commands(active_plugin_only: bool = True) -> dict[str, Any]:
    commands: dict[str, Any] = {}
    for spec in iter_plugin_command_specs(active_plugin_only=active_plugin_only):
        commands[spec.command_id] = create_freecad_command(spec)
    return commands


def create_freecad_command(spec: PluginCommandSpec) -> Any:
    if spec.command_type == "place_component" and spec.component is not None:
        from ocw_workbench.commands.place_component_type import PlaceComponentTypeCommand

        return PlaceComponentTypeCommand(spec.component, spec=spec)
    raise KeyError(f"Unsupported plugin command type: {spec.command_type}")


def _command_metadata(active_plugin_only: bool = True) -> dict[str, dict[str, Any]]:
    plugin_service = get_plugin_service()
    if active_plugin_only:
        command_set = plugin_service.get_commands_for_active_plugin()
        return command_set.get("commands", {}) if isinstance(command_set, dict) else {}

    merged: dict[str, dict[str, Any]] = {}
    registry = plugin_service.registry()
    for command_set in registry.command_sets().values():
        if not isinstance(command_set, dict):
            continue
        commands = command_set.get("commands", {})
        if not isinstance(commands, dict):
            continue
        for command_id, metadata in commands.items():
            if isinstance(metadata, dict):
                merged[str(command_id)] = metadata
    return merged


def _build_spec(command_key: str, metadata: dict[str, Any]) -> PluginCommandSpec:
    label = str(metadata.get("label") or _humanize_command_id(command_key))
    tooltip = str(metadata.get("tooltip") or label)
    if label not in tooltip:
        tooltip = f"{label}. {tooltip}"
    component = str(metadata.get("component")) if metadata.get("component") is not None else None
    return PluginCommandSpec(
        id=str(metadata.get("id") or command_key),
        command_id=str(metadata.get("command_id") or _default_command_id(metadata, command_key)),
        command_type=str(metadata.get("type") or "plugin"),
        label=label,
        tooltip=tooltip,
        icon=str(metadata.get("icon") or "generic.svg"),
        category=str(metadata.get("category") or "Plugin"),
        component=component,
        library_ref=str(metadata.get("library_ref")) if metadata.get("library_ref") is not None else None,
        plugin_id=str(metadata.get("plugin_id")) if metadata.get("plugin_id") is not None else None,
    )


def _humanize_command_id(command_id: str) -> str:
    return str(command_id).replace("_", " ").strip().title() or "Plugin Command"


def _default_command_id(metadata: dict[str, Any], command_key: str) -> str:
    component = metadata.get("component")
    if isinstance(component, str) and component:
        suffix = component.replace("_", " ").title().replace(" ", "")
        return f"OCW_Place{suffix}"
    return f"OCW_{_humanize_command_id(command_key).replace(' ', '')}"
