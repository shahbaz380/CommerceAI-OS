"""Plugin discovery/loader placeholder.

Does not execute untrusted code. Future: load manifests from plugins/registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config.settings import AppSettings, get_settings
from app.infrastructure.logging.setup import get_logger

logger = get_logger("app")


@dataclass(slots=True)
class PluginManifest:
    id: str
    version: str
    display_name: str
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class PluginLoader:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._plugins: dict[str, PluginManifest] = {}

    @property
    def runtime_enabled(self) -> bool:
        return self._settings.feature_plugin_runtime

    def register_manifest(self, manifest: PluginManifest) -> None:
        self._plugins[manifest.id] = manifest
        logger.info("plugin_registered", plugin_id=manifest.id, version=manifest.version)

    def list_plugins(self) -> list[PluginManifest]:
        return list(self._plugins.values())

    def load_enabled(self) -> list[PluginManifest]:
        if not self.runtime_enabled:
            logger.info("plugin_runtime_disabled")
            return []
        enabled = [p for p in self._plugins.values() if p.enabled]
        logger.info("plugins_loaded", count=len(enabled))
        return enabled


_loader: PluginLoader | None = None


def get_plugin_loader(settings: AppSettings | None = None) -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader(settings or get_settings())
    return _loader
