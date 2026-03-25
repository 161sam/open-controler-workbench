from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from ocf_freecad.plugin_api.types import PluginDescriptor


class ExtensionRegistry:
    def __init__(self) -> None:
        self._plugin_descriptors: dict[str, PluginDescriptor] = {}
        self._sources: dict[str, list[Path]] = defaultdict(list)
        self._providers: dict[str, dict[str, Any]] = defaultdict(dict)

    def register_plugin(self, descriptor: PluginDescriptor) -> None:
        self._plugin_descriptors[descriptor.plugin_id] = descriptor

    def has_plugin(self, plugin_id: str) -> bool:
        return plugin_id in self._plugin_descriptors

    def register_source(self, registry_name: str, source: Path) -> None:
        if source not in self._sources[registry_name]:
            self._sources[registry_name].append(source)

    def register_provider(self, registry_name: str, provider_id: str, provider: Any) -> None:
        self._providers[registry_name][provider_id] = provider

    def plugin_descriptors(self) -> list[PluginDescriptor]:
        return list(self._plugin_descriptors.values())

    def plugin_descriptor(self, plugin_id: str) -> PluginDescriptor:
        return self._plugin_descriptors[plugin_id]

    def sources(self, registry_name: str) -> list[Path]:
        return list(self._sources.get(registry_name, []))

    def component_sources(self) -> list[Path]:
        return self.sources("components")

    def template_sources(self) -> list[Path]:
        return self.sources("templates")

    def variant_sources(self) -> list[Path]:
        return self.sources("variants")

    def providers(self, registry_name: str) -> dict[str, Any]:
        return deepcopy(self._providers.get(registry_name, {}))

    def exporters(self) -> dict[str, Any]:
        return self.providers("exporters")

    def layout_strategies(self) -> dict[str, Any]:
        return self.providers("layout_strategies")

    def constraints(self) -> dict[str, Any]:
        return self.providers("constraints")
