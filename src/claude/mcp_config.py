"""MCP Server configuration management."""

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class McpServerEntry:
    """An MCP server configuration entry."""

    name: str
    enabled: bool
    config: dict[str, Any]


@dataclass
class McpConfig:
    """Full MCP configuration."""

    version: int = 1
    servers: dict[str, dict[str, Any]] = field(default_factory=dict)


class McpConfigManager:
    """Manages MCP server configurations with persistent storage."""

    CONFIG_DIR = Path.home() / ".local" / "share" / "claude-sdk-tutor"
    CONFIG_FILE = CONFIG_DIR / "mcp_servers.json"

    def __init__(self):
        self._config: McpConfig = McpConfig()
        self._load()

    def _load(self) -> None:
        """Load configuration from disk."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE) as f:
                    data = json.load(f)
                self._config = McpConfig(
                    version=data.get("version", 1),
                    servers=data.get("servers", {}),
                )
            except (json.JSONDecodeError, OSError):
                self._config = McpConfig()
        else:
            self._config = McpConfig()

    def _save(self) -> None:
        """Save configuration to disk."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(
                {"version": self._config.version, "servers": self._config.servers},
                f,
                indent=2,
            )

    def list_servers(self) -> list[McpServerEntry]:
        """List all configured servers."""
        entries = []
        for name, data in self._config.servers.items():
            entries.append(
                McpServerEntry(
                    name=name,
                    enabled=data.get("enabled", True),
                    config=data.get("config", {}),
                )
            )
        return entries

    def get_server(self, name: str) -> McpServerEntry | None:
        """Get a specific server by name."""
        if name not in self._config.servers:
            return None
        data = self._config.servers[name]
        return McpServerEntry(
            name=name,
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
        )

    def add_server(self, name: str, config: dict[str, Any]) -> None:
        """Add a new server configuration."""
        self._config.servers[name] = {"enabled": True, "config": config}
        self._save()

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration. Returns True if removed."""
        if name in self._config.servers:
            del self._config.servers[name]
            self._save()
            return True
        return False

    def enable_server(self, name: str) -> bool:
        """Enable a server. Returns True if server exists."""
        if name in self._config.servers:
            self._config.servers[name]["enabled"] = True
            self._save()
            return True
        return False

    def disable_server(self, name: str) -> bool:
        """Disable a server. Returns True if server exists."""
        if name in self._config.servers:
            self._config.servers[name]["enabled"] = False
            self._save()
            return True
        return False

    def _expand_env_vars(self, value: Any) -> Any:
        """Recursively expand environment variables in config values."""
        if isinstance(value, str):
            # Match ${VAR_NAME} pattern
            pattern = r"\$\{([^}]+)\}"
            matches = re.findall(pattern, value)
            result = value
            for var_name in matches:
                env_value = os.environ.get(var_name, "")
                result = result.replace(f"${{{var_name}}}", env_value)
            return result
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        return value

    def get_enabled_servers_for_sdk(self) -> dict[str, dict[str, Any]]:
        """Get enabled servers in SDK-compatible format with env vars expanded."""
        result = {}
        for name, data in self._config.servers.items():
            if data.get("enabled", True):
                config = data.get("config", {})
                result[name] = self._expand_env_vars(config)
        return result
