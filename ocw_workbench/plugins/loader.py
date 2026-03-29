from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType
from typing import Callable

from ocw_workbench.plugins.registry import ExtensionRegistry, Plugin
from ocw_workbench.plugin_api.types import PluginDescriptor
from ocw_workbench.plugins.context import PluginContext
from ocw_workbench.plugins.hooks import run_module_hooks
from ocw_workbench.plugins.manifest import load_plugin_manifest
from ocw_workbench.utils.yaml_io import load_yaml

LOGGER = logging.getLogger(__name__)


class PluginLoader:
    def __init__(
        self,
        internal_root: str | Path | None = None,
        external_root: str | Path | None = None,
        domain_root: str | Path | None = None,
        enabled_resolver: Callable[[PluginDescriptor], bool] | None = None,
    ) -> None:
        base = Path(__file__).resolve().parent
        self.internal_root = Path(internal_root or (base / "internal"))
        self.external_root = Path(external_root or (base / "external"))
        self.domain_root = Path(domain_root or (base.parent.parent / "plugins"))
        self.enabled_resolver = enabled_resolver
        self.registry = ExtensionRegistry()
        self.warnings: list[str] = []
        self._loaded = False

    def load_all(self) -> ExtensionRegistry:
        if self._loaded:
            return self.registry

        for plugin in self.scan_plugins():
            if self.registry.has_plugin(plugin.plugin_id):
                self.warnings.append(f"Skipping duplicate plugin id '{plugin.plugin_id}'")
                continue
            self.registry.register_plugin(plugin)

        pending: list[PluginDescriptor] = []
        pending.extend(self._discover_from_root(self.internal_root))
        pending.extend(self._discover_from_root(self.external_root))

        while pending:
            progress = False
            remaining: list[PluginDescriptor] = []
            pending_ids = {descriptor.plugin_id for descriptor in pending}
            for descriptor in pending:
                if not self._is_enabled(descriptor):
                    progress = True
                    continue
                if self._dependencies_missing(descriptor, pending_ids):
                    remaining.append(descriptor)
                    continue
                if self.registry.has_plugin(descriptor.plugin_id):
                    self.warnings.append(f"Skipping duplicate plugin id '{descriptor.plugin_id}'")
                    progress = True
                    continue
                self.registry.register_plugin(descriptor)
                context = PluginContext(
                    registry=self.registry,
                    config={"plugin_id": descriptor.plugin_id},
                    warnings=self.warnings,
                )
                self._register_manifest_entrypoints(descriptor, context)
                self._run_hook_module(descriptor, context)
                progress = True

            if not progress:
                for descriptor in remaining:
                    missing = [
                        dependency for dependency in descriptor.dependencies if not self.registry.has_plugin(dependency)
                    ]
                    self.warnings.append(
                        f"Skipping plugin '{descriptor.plugin_id}' because dependencies are missing: {', '.join(sorted(missing))}"
                    )
                break
            pending = remaining

        self._ensure_default_active_plugin()
        self._loaded = True
        return self.registry

    def scan_plugins(self) -> list[Plugin]:
        if not self.domain_root.exists():
            return []

        plugins: list[Plugin] = []
        for plugin_dir in sorted(item for item in self.domain_root.iterdir() if item.is_dir()):
            manifest_path = plugin_dir / "plugin.yaml"
            if not manifest_path.exists():
                continue
            try:
                plugins.append(self._load_scanned_plugin(manifest_path))
            except Exception as exc:
                self.warnings.append(f"Failed to scan plugin manifest '{manifest_path}': {exc}")
        return plugins

    def _is_enabled(self, descriptor: PluginDescriptor) -> bool:
        if descriptor.non_disableable:
            return True
        if self.enabled_resolver is None:
            return True
        return bool(self.enabled_resolver(descriptor))

    def _discover_from_root(self, root: Path) -> list[PluginDescriptor]:
        if not root.exists():
            return []

        descriptors: list[PluginDescriptor] = []
        for plugin_dir in sorted(item for item in root.iterdir() if item.is_dir()):
            manifest_path = self._manifest_path(plugin_dir)
            if not manifest_path.exists():
                self.warnings.append(f"Skipping plugin without manifest: {plugin_dir}")
                continue
            try:
                descriptor = load_plugin_manifest(manifest_path)
            except Exception as exc:
                self.warnings.append(f"Failed to load plugin manifest '{manifest_path}': {exc}")
                continue
            descriptors.append(descriptor)
        return descriptors

    def _dependencies_missing(self, descriptor: PluginDescriptor, pending_ids: set[str]) -> bool:
        missing = []
        for dependency in descriptor.dependencies:
            if self.registry.has_plugin(dependency):
                continue
            missing.append(dependency)
            if dependency in pending_ids:
                return True
        return bool(missing)

    def _register_manifest_entrypoints(self, descriptor: PluginDescriptor, context: PluginContext) -> None:
        mapping = {
            "components": descriptor.entrypoints.components,
            "templates": descriptor.entrypoints.templates,
            "variants": descriptor.entrypoints.variants,
            "exporters": descriptor.entrypoints.exporters,
            "layout_strategies": descriptor.entrypoints.layouts,
            "constraints": descriptor.entrypoints.constraints,
        }
        for registry_name, relative_path in mapping.items():
            if relative_path is None or descriptor.root_path is None:
                continue
            source = (descriptor.root_path / relative_path).resolve()
            if source.exists():
                context.register_source(registry_name, source, plugin_id=descriptor.plugin_id)
            else:
                context.warn(f"Plugin '{descriptor.plugin_id}' entrypoint '{registry_name}' not found: {source}")

    def _run_hook_module(self, descriptor: PluginDescriptor, context: PluginContext) -> None:
        if descriptor.entrypoints.module is None or descriptor.root_path is None:
            return
        module_path = (descriptor.root_path / descriptor.entrypoints.module).resolve()
        if not module_path.exists():
            context.warn(f"Plugin '{descriptor.plugin_id}' hook module not found: {module_path}")
            return
        try:
            module = self._load_module(module_path, descriptor.plugin_id)
        except Exception as exc:
            context.warn(f"Plugin '{descriptor.plugin_id}' failed to import hooks: {exc}")
            return
        run_module_hooks(module, context)

    def _load_module(self, module_path: Path, plugin_id: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(f"ocw_plugin_{plugin_id}", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to create spec for {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _manifest_path(self, plugin_dir: Path) -> Path:
        for filename in ("plugin.yaml", "manifest.yaml"):
            path = plugin_dir / filename
            if path.exists():
                return path
        return plugin_dir / "manifest.yaml"

    def _load_scanned_plugin(self, manifest_path: Path) -> Plugin:
        payload = load_yaml(manifest_path)
        plugin_data = payload.get("plugin") if isinstance(payload.get("plugin"), dict) else payload
        if not isinstance(plugin_data, dict):
            raise ValueError("Plugin manifest must be a mapping")

        plugin_id = self._require_str(plugin_data.get("id"), "id", manifest_path)
        plugin_type = self._require_str(plugin_data.get("type"), "type", manifest_path)
        name = self._require_str(plugin_data.get("name"), "name", manifest_path)
        version = self._require_str(plugin_data.get("version"), "version", manifest_path)
        raw_dependencies = plugin_data.get("depends_on", plugin_data.get("dependencies", []))
        if raw_dependencies is None:
            raw_dependencies = []
        if not isinstance(raw_dependencies, list):
            raise ValueError("depends_on must be a list")
        root_path = manifest_path.parent

        return Plugin(
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            name=name,
            version=version,
            dependencies=tuple(str(item) for item in raw_dependencies),
            domain_type=str(plugin_data.get("domain_type") or plugin_id) if plugin_type == "domain" else None,
            provides_templates=self._capability_flag(plugin_data, "provides_templates", root_path / "templates"),
            provides_components=self._capability_flag(plugin_data, "provides_components", root_path / "components"),
            provides_commands=self._capability_flag(plugin_data, "provides_commands", root_path / "commands"),
            root_path=root_path,
            manifest_path=manifest_path,
            raw_manifest=payload if isinstance(payload, dict) else {"plugin": plugin_data},
        )

    def _require_str(self, value: object, field: str, manifest_path: Path) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing required field '{field}' in {manifest_path}")
        return value

    def _capability_flag(self, plugin_data: dict[str, object], field: str, default_path: Path) -> bool:
        if field in plugin_data:
            return bool(plugin_data[field])
        return default_path.exists()

    def _ensure_default_active_plugin(self) -> None:
        if self.registry.get_active_plugin() is not None:
            return
        preferred_plugin = self.registry.plugin("midicontroller") if self.registry.has_plugin("midicontroller") else None
        if preferred_plugin is not None and preferred_plugin.plugin_type == "domain":
            self.registry.set_active_plugin(preferred_plugin.plugin_id)
            LOGGER.debug("Soft-activated default domain plugin '%s'.", preferred_plugin.plugin_id)
            return
        domain_plugins = self.registry.get_domain_plugins()
        if len(domain_plugins) == 1:
            self.registry.set_active_plugin(domain_plugins[0].plugin_id)
            LOGGER.debug("Soft-activated sole domain plugin '%s'.", domain_plugins[0].plugin_id)
