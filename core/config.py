"""Configuration manager module.

Provides hot-reloadable runtime configuration from YAML.
Every threshold, language, timing, SLA rule, role, holiday list, and weight
is centralized and reloadable.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("config/default.yaml")


@dataclass
class AppConfig:
    """Strongly typed container for application configuration."""

    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def timezone(self) -> str:
        return self.raw_data.get("timezone", "Asia/Kolkata")

    @property
    def languages(self) -> list[str]:
        return list(self.raw_data.get("languages", ["en"]))

    @property
    def timings(self) -> dict[str, Any]:
        return dict(self.raw_data.get("timings", {}))

    @property
    def sla_rules(self) -> dict[str, Any]:
        return dict(self.raw_data.get("sla_rules", {}))

    @property
    def roles(self) -> dict[str, Any]:
        return dict(self.raw_data.get("roles", {}))

    @property
    def api_keys(self) -> dict[str, str]:
        result = dict(self.raw_data.get("api_keys", {}))
        for role in self.roles:
            key = os.getenv(f"API_KEY_{role.upper()}")
            if key:
                result[key] = role
        return result

    @property
    def holidays(self) -> list[str]:
        return list(self.raw_data.get("holidays", []))

    @property
    def weights(self) -> dict[str, float]:
        return dict(self.raw_data.get("weights", {}))

    @property
    def thresholds(self) -> dict[str, Any]:
        return dict(self.raw_data.get("thresholds", {}))

    @property
    def retention(self) -> dict[str, Any]:
        return dict(self.raw_data.get("retention", {}))

    def get(self, key_path: str, default: Any = None) -> Any:
        """Fetch nested configuration via dot notation (e.g. 'thresholds.similarity_threshold')."""
        parts = key_path.split(".")
        current = self.raw_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current


class ConfigManager:
    """Manages application configuration with hot-reloading capabilities."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        env_path = os.getenv("CONFIG_PATH")
        if config_path is not None:
            self._path = Path(config_path)
        elif env_path:
            self._path = Path(env_path)
        else:
            self._path = DEFAULT_CONFIG_PATH

        self._last_mtime: float = 0.0
        self._runtime_overrides: dict[str, Any] = {}
        self._config: AppConfig = AppConfig()
        self.reload(force=True)

    @property
    def config(self) -> AppConfig:
        """Return current configuration, auto-checking if underlying file changed."""
        self._check_and_reload()
        return self._config

    def _check_and_reload(self) -> None:
        if self._path.exists():
            current_mtime = self._path.stat().st_mtime
            if current_mtime > self._last_mtime:
                self.reload(force=True)

    def reload(self, force: bool = False) -> None:
        """Reload configuration from disk."""
        if not self._path.exists():
            if force:
                self._config = AppConfig(raw_data={})
            return

        current_mtime = self._path.stat().st_mtime
        if force or current_mtime > self._last_mtime:
            with open(self._path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self._config = AppConfig(raw_data=data)
            self._last_mtime = current_mtime
            for key_path, value in self._runtime_overrides.items():
                self.update_runtime_override(key_path, value)

    def update_runtime_override(self, key_path: str, value: Any) -> None:
        """Apply in-memory override for testing without writing to file."""
        self._runtime_overrides[key_path] = value
        parts = key_path.split(".")
        target = self._config.raw_data
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value

    def has_runtime_override(self, key_path: str) -> bool:
        return key_path in self._runtime_overrides


_GLOBAL_CONFIG_MANAGER: ConfigManager | None = None


def get_config_manager(config_path: str | Path | None = None) -> ConfigManager:
    """Return singleton ConfigManager instance."""
    global _GLOBAL_CONFIG_MANAGER
    if _GLOBAL_CONFIG_MANAGER is None or config_path is not None:
        _GLOBAL_CONFIG_MANAGER = ConfigManager(config_path)
    return _GLOBAL_CONFIG_MANAGER


def get_config() -> AppConfig:
    """Shortcut to get current AppConfig."""
    return get_config_manager().config
