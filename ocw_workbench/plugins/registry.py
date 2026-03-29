from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from ocw_workbench.plugin_api.types import PluginDescriptor
from ocw_workbench.utils.yaml_io import load_yaml


@dataclass(frozen=True)
class PluginSource:
    plugin_id: str | None
    path: Path


@dataclass(frozen=True)
class Plugin:
    plugin_id: str
    name: str
    version: str
    plugin_type: str
    dependencies: tuple[str, ...] = ()
    domain_type: str | None = None
    provides_templates: bool = False
    provides_components: bool = False
    provides_commands: bool = False
    root_path: Path | None = None
    manifest_path: Path | None = None
    raw_manifest: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "type": self.plugin_type,
            "dependencies": list(self.dependencies),
            "domain_type": self.domain_type,
            "provides_templates": self.provides_templates,
            "provides_components": self.provides_components,
            "provides_commands": self.provides_commands,
            "root_path": str(self.root_path) if self.root_path is not None else None,
            "manifest_path": str(self.manifest_path) if self.manifest_path is not None else None,
            "raw_manifest": deepcopy(self.raw_manifest) if self.raw_manifest is not None else None,
        }

    def template_root(self) -> Path | None:
        if not self.provides_templates or self.root_path is None:
            return None
        candidate = self.root_path / "templates"
        return candidate if candidate.exists() else None

    def component_root(self) -> Path | None:
        if not self.provides_components or self.root_path is None:
            return None
        candidate = self.root_path / "components"
        return candidate if candidate.exists() else None

    def commands_root(self) -> Path | None:
        if not self.provides_commands or self.root_path is None:
            return None
        candidate = self.root_path / "commands"
        return candidate if candidate.exists() else None

    def variant_root(self) -> Path | None:
        if self.root_path is None:
            return None
        candidate = self.root_path / "variants"
        return candidate if candidate.exists() else None


class ExtensionRegistry:
    def __init__(self) -> None:
        self._plugin_descriptors: dict[str, PluginDescriptor] = {}
        self._plugins: dict[str, Plugin] = {}
        self._sources: dict[str, list[PluginSource]] = defaultdict(list)
        self._providers: dict[str, dict[str, Any]] = defaultdict(dict)
        self._command_sets: dict[str, dict[str, Any]] = {}
        self.active_domain_plugin: Plugin | None = None

    def register_plugin(self, descriptor: PluginDescriptor | Plugin) -> None:
        if isinstance(descriptor, PluginDescriptor):
            plugin = Plugin(
                plugin_id=descriptor.plugin_id,
                name=descriptor.name,
                version=descriptor.version,
                plugin_type=descriptor.plugin_type,
                dependencies=tuple(descriptor.dependencies),
                domain_type=descriptor.domain_type,
                provides_templates=descriptor.provides_templates,
                provides_components=descriptor.provides_components,
                provides_commands=descriptor.provides_commands,
                root_path=descriptor.root_path,
                manifest_path=None,
                raw_manifest=descriptor.to_dict(),
            )
            self._plugin_descriptors[descriptor.plugin_id] = descriptor
            self._plugins[descriptor.plugin_id] = plugin
            self._register_command_set(plugin)
            return
        self._plugins[descriptor.plugin_id] = descriptor
        self._register_command_set(descriptor)

    def has_plugin(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins

    def register_source(self, registry_name: str, source: Path, plugin_id: str | None = None) -> None:
        entry = PluginSource(plugin_id=plugin_id, path=source)
        if entry not in self._sources[registry_name]:
            self._sources[registry_name].append(entry)

    def register_provider(self, registry_name: str, provider_id: str, provider: Any) -> None:
        self._providers[registry_name][provider_id] = provider
        if registry_name == "commands":
            self._command_sets[provider_id] = deepcopy(provider)

    def plugin_descriptors(self) -> list[PluginDescriptor]:
        return list(self._plugin_descriptors.values())

    def plugins(self) -> list[Plugin]:
        return list(self._plugins.values())

    def plugin(self, plugin_id: str) -> Plugin:
        return self._plugins[plugin_id]

    def plugin_descriptor(self, plugin_id: str) -> PluginDescriptor:
        return self._plugin_descriptors[plugin_id]

    def set_active_plugin(self, plugin_id: str) -> Plugin:
        plugin = self.plugin(plugin_id)
        if plugin.plugin_type != "domain":
            raise ValueError(f"Plugin '{plugin_id}' is not a domain plugin")
        self.active_domain_plugin = plugin
        return plugin

    def get_active_plugin(self) -> Plugin | None:
        return self.active_domain_plugin

    def get_domain_plugins(self) -> list[Plugin]:
        return [plugin for plugin in self._plugins.values() if plugin.plugin_type == "domain"]

    def get_active_domain(self) -> str | None:
        plugin = self.get_active_plugin()
        return plugin.domain_type if plugin is not None else None

    def get_template_roots(self, plugin_id: str | None = None) -> list[Path]:
        plugin = self._resolve_target_plugin(plugin_id)
        roots: list[Path] = []
        if plugin is not None:
            template_root = plugin.template_root()
            if template_root is not None:
                roots.append(template_root)
        roots.extend(self.template_sources())
        return _dedupe_paths(roots)

    def get_component_registries(self, plugin_id: str | None = None) -> list[Path]:
        plugin = self._resolve_target_plugin(plugin_id)
        roots: list[Path] = []
        if plugin is not None:
            component_root = plugin.component_root()
            if component_root is not None:
                roots.append(component_root)
        roots.extend(self.component_sources())
        return _dedupe_paths(roots)

    def get_commands_for_active_plugin(self) -> dict[str, Any]:
        plugin = self.get_active_plugin()
        if plugin is None:
            return {}
        return deepcopy(self._command_sets.get(plugin.plugin_id, {}))

    def command_sets(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self._command_sets)

    def command_plugin_mapping(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for plugin_id, command_set in self._command_sets.items():
            for command_id in command_set.get("commands", {}):
                mapping[str(command_id)] = plugin_id
        return mapping

    def sources(self, registry_name: str) -> list[Path]:
        return [entry.path for entry in self._sources.get(registry_name, [])]

    def source_entries(self, registry_name: str) -> list[PluginSource]:
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

    def _resolve_target_plugin(self, plugin_id: str | None) -> Plugin | None:
        if plugin_id is not None:
            return self._plugins.get(plugin_id)
        return self.get_active_plugin()

    def _register_command_set(self, plugin: Plugin) -> None:
        commands_root = plugin.commands_root()
        if commands_root is None:
            self._command_sets.setdefault(
                plugin.plugin_id,
                {
                    "plugin_id": plugin.plugin_id,
                    "root": None,
                    "commands": {},
                },
            )
            return
        self._command_sets[plugin.plugin_id] = {
            "plugin_id": plugin.plugin_id,
            "root": str(commands_root),
            "commands": _discover_command_metadata(commands_root, plugin.plugin_id),
        }


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped


def _discover_command_metadata(commands_root: Path, plugin_id: str | None = None) -> dict[str, dict[str, Any]]:
    commands: dict[str, dict[str, Any]] = {}
    for file_path in sorted(commands_root.glob("*.yaml")):
        metadata = _load_structured_command_metadata(file_path)
        if metadata is None:
            continue
        metadata.setdefault("plugin_id", plugin_id)
        command_id = str(metadata.get("id") or file_path.stem)
        commands[command_id] = metadata
    for file_path in sorted(commands_root.glob("*.json")):
        metadata = _load_structured_command_metadata(file_path)
        if metadata is None:
            continue
        metadata.setdefault("plugin_id", plugin_id)
        command_id = str(metadata.get("id") or file_path.stem)
        commands[command_id] = metadata
    for file_path in sorted(commands_root.glob("*.py")):
        if file_path.name == "__init__.py":
            continue
        command_id = file_path.stem
        commands.setdefault(command_id, {
            "id": command_id,
            "label": _humanize_command_id(command_id),
            "icon": "default",
            "category": "plugin",
            "tooltip": _humanize_command_id(command_id),
            "module_path": str(file_path),
            "plugin_id": plugin_id,
        })
    return commands


def _humanize_command_id(command_id: str) -> str:
    return str(command_id).replace("_", " ").strip().title() or "Plugin Command"


def _load_structured_command_metadata(path: Path) -> dict[str, Any] | None:
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = load_yaml(path)
    if not isinstance(payload, dict):
        return None
    metadata = deepcopy(payload)
    metadata.setdefault("module_path", None)
    return metadata
