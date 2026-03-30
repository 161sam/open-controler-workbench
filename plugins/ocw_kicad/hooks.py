from __future__ import annotations

from ocw_workbench.plugins.context import PluginContext

from plugins.ocw_kicad.plugin import build_roundtrip_import_descriptor


def register_layout_strategies(context: PluginContext) -> None:
    context.register_provider("layout_strategies", "kicad_stepup_board_import", build_roundtrip_import_descriptor)
