from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ocw_workbench.plugins.registry import ExtensionRegistry, Plugin


@dataclass
class PluginContext:
    registry: ExtensionRegistry
    config: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def register_source(self, registry_name: str, source: str | Path, plugin_id: str | None = None) -> None:
        self.registry.register_source(registry_name, Path(source), plugin_id=plugin_id)

    def register_provider(self, registry_name: str, provider_id: str, provider: Any) -> None:
        self.registry.register_provider(registry_name, provider_id, provider)

    def get_active_plugin(self) -> Plugin | None:
        return self.registry.get_active_plugin()

    def get_active_domain(self) -> str | None:
        return self.registry.get_active_domain()

    def template_roots(self) -> list[Path]:
        return self.registry.get_template_roots()

    def component_registries(self) -> list[Path]:
        return self.registry.get_component_registries()

    def command_sets(self) -> dict[str, dict[str, Any]]:
        return self.registry.command_sets()

    def get_commands_for_active_plugin(self) -> dict[str, Any]:
        return self.registry.get_commands_for_active_plugin()

    def command_plugin_mapping(self) -> dict[str, str]:
        return self.registry.command_plugin_mapping()

    def warn(self, message: str) -> None:
        self.warnings.append(message)
