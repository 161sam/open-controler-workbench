from __future__ import annotations

import logging

from ocw_workbench.plugins.registry import ExtensionRegistry, Plugin
from ocw_workbench.services.plugin_service import get_plugin_service

LOGGER = logging.getLogger(__name__)


def activate_plugin(plugin_id: str, registry: ExtensionRegistry | None = None) -> Plugin:
    active_registry = registry or get_plugin_service().registry()
    if not active_registry.has_plugin(plugin_id):
        raise KeyError(f"Unknown plugin id: {plugin_id}")
    plugin = active_registry.plugin(plugin_id)
    if plugin.plugin_type != "domain":
        raise ValueError(f"Plugin '{plugin_id}' is not a domain plugin")
    for dependency in plugin.dependencies:
        LOGGER.info("Plugin activation dependency stub for '%s': %s", plugin_id, dependency)
    return active_registry.set_active_plugin(plugin_id)
