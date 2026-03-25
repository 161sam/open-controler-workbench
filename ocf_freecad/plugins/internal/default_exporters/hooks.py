from __future__ import annotations

from pathlib import Path
from typing import Any

from ocf_freecad.exporters.assembly_exporter import export_assembly
from ocf_freecad.exporters.bom_exporter import export_bom_csv, export_bom_yaml
from ocf_freecad.exporters.electrical_exporter import export_electrical_mapping
from ocf_freecad.exporters.manufacturing_exporter import export_manufacturing
from ocf_freecad.exporters.schematic_exporter import export_schematic
from ocf_freecad.plugins.context import PluginContext
from ocf_freecad.utils.yaml_io import dump_yaml


def register_exporters(context: PluginContext) -> None:
    context.register_provider("exporters", "kicad_layout", export_kicad_layout)
    context.register_provider("exporters", "electrical_mapping", export_electrical_mapping)
    context.register_provider("exporters", "schematic", export_schematic)
    context.register_provider("exporters", "bom_yaml", export_bom_yaml)
    context.register_provider("exporters", "bom_csv", export_bom_csv)
    context.register_provider("exporters", "manufacturing", export_manufacturing)
    context.register_provider("exporters", "assembly", export_assembly)


def export_kicad_layout(data: dict[str, Any], path: str | Path) -> None:
    dump_yaml(path, data)
