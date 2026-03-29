from __future__ import annotations

from typing import Any

from ocw_workbench.commands.factory import component_toolbar_command_ids, component_toolbar_groups


def build_plugin_toolbars(active_plugin_id: str | None = None) -> list[tuple[str, list[str]]]:
    return component_toolbar_groups(active_plugin_id=active_plugin_id)


def build_primary_component_toolbar() -> list[str]:
    return component_toolbar_command_ids() + ["OCW_OpenComponentPalette"]


def append_plugin_toolbars(workbench: Any, active_plugin_id: str | None = None) -> list[tuple[str, list[str]]]:
    toolbars = build_plugin_toolbars(active_plugin_id=active_plugin_id)
    for toolbar_name, commands in toolbars:
        workbench.appendToolbar(toolbar_name, commands)
    return toolbars
