from __future__ import annotations

from pathlib import Path

from ocf_freecad.plugins.loader import PluginLoader
from ocf_freecad.plugins.registry import ExtensionRegistry

_PLUGIN_SERVICE: PluginService | None = None


class PluginService:
    def __init__(self, loader: PluginLoader | None = None) -> None:
        self.loader = loader or PluginLoader()

    def registry(self) -> ExtensionRegistry:
        return self.loader.load_all()

    def warnings(self) -> list[str]:
        self.loader.load_all()
        return list(self.loader.warnings)

    def component_sources(self) -> list[Path]:
        return self.registry().component_sources()

    def template_sources(self) -> list[Path]:
        return self.registry().template_sources()

    def variant_sources(self) -> list[Path]:
        return self.registry().variant_sources()

    def exporters(self) -> dict[str, object]:
        return self.registry().exporters()

    def layout_strategies(self) -> dict[str, object]:
        return self.registry().layout_strategies()

    def constraints(self) -> dict[str, object]:
        return self.registry().constraints()


def get_plugin_service() -> PluginService:
    global _PLUGIN_SERVICE
    if _PLUGIN_SERVICE is None:
        _PLUGIN_SERVICE = PluginService()
    return _PLUGIN_SERVICE


def reset_plugin_service(
    internal_root: str | Path | None = None,
    external_root: str | Path | None = None,
) -> PluginService:
    global _PLUGIN_SERVICE
    _PLUGIN_SERVICE = PluginService(loader=PluginLoader(internal_root=internal_root, external_root=external_root))
    return _PLUGIN_SERVICE
