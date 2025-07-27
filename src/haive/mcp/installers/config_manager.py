"""MCP Configuration and Environment Management

Handles .env files, configuration templates, and secure credential storage.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, SecretStr


class MCPEnvironmentConfig(BaseModel):
    """Environment configuration for MCP servers"""

    # Basic server info
    server_name: str = Field(description="Unique server identifier")
    package_name: str = Field(description="NPM package or Python module name")

    # Environment variables
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    secure_vars: dict[str, SecretStr] = Field(
        default_factory=dict, description="Secure environment variables"
    )

    # Server configuration
    startup_args: list[str] = Field(
        default_factory=list, description="Command line arguments"
    )
    working_directory: str | None = Field(
        default=None, description="Working directory for server"
    )

    # Transport settings
    transport_type: str = Field(default="stdio", description="stdio, http, websocket")
    port: int | None = Field(
        default=None, description="Port for HTTP/WebSocket transports"
    )

    # Security settings
    allowed_paths: list[str] = Field(
        default_factory=list, description="Allowed filesystem paths"
    )
    requires_approval: bool = Field(
        default=True, description="Require human approval for installation"
    )


@dataclass
class MCPServerPattern:
    """Standard pattern for MCP server installation"""

    pattern_name: str
    package_pattern: str  # e.g., "@modelcontextprotocol/server-*"
    install_command: str  # e.g., "npx -y {package_name}"
    startup_command: str  # e.g., "npx -y {package_name} {args}"
    default_args: list[str]
    env_template: dict[str, str]
    transport: str = "stdio"
    security_level: str = "safe"  # safe, moderate, high_risk


class MCPConfigManager:
    """Manages MCP server configurations and environment files"""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".haive" / "mcp"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.env_file = self.config_dir / ".env"
        self.servers_config = self.config_dir / "servers.json"
        self.patterns_config = self.config_dir / "patterns.json"

        self._load_or_create_defaults()

    def _load_or_create_defaults(self):
        """Load existing configs or create defaults"""
        if not self.patterns_config.exists():
            self._create_default_patterns()

        if not self.servers_config.exists():
            self._create_default_servers_config()

    def _create_default_patterns(self):
        """Create default MCP server patterns"""
        default_patterns = {
            "filesystem": {
                "pattern_name": "filesystem",
                "package_pattern": "@modelcontextprotocol/server-filesystem",
                "install_command": "none",  # npx handles installation
                "startup_command": "npx -y {package_name} {args}",
                "default_args": ["/tmp"],
                "env_template": {},
                "transport": "stdio",
                "security_level": "safe",
            },
            "database": {
                "pattern_name": "database",
                "package_pattern": "@modelcontextprotocol/server-*database*",
                "install_command": "none",
                "startup_command": "npx -y {package_name}",
                "default_args": [],
                "env_template": {
                    "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
                },
                "transport": "stdio",
                "security_level": "moderate",
            },
            "web_api": {
                "pattern_name": "web_api",
                "package_pattern": "@modelcontextprotocol/server-*",
                "install_command": "none",
                "startup_command": "npx -y {package_name}",
                "default_args": [],
                "env_template": {
                    "API_KEY": "your_api_key_here",
                    "BASE_URL": "https://api.example.com",
                },
                "transport": "stdio",
                "security_level": "moderate",
            },
            "python_server": {
                "pattern_name": "python_server",
                "package_pattern": "mcp-server-*",
                "install_command": "pip install {package_name}",
                "startup_command": "python -m {module_name}",
                "default_args": [],
                "env_template": {},
                "transport": "stdio",
                "security_level": "safe",
            },
        }

        with open(self.patterns_config, "w") as f:
            json.dump(default_patterns, f, indent=2)

    def _create_default_servers_config(self):
        """Create default servers configuration"""
        default_config = {
            "version": "1.0",
            "servers": {},
            "global_settings": {
                "require_approval_by_default": True,
                "max_startup_timeout": 30,
                "log_level": "INFO",
            },
        }

        with open(self.servers_config, "w") as f:
            json.dump(default_config, f, indent=2)

    def get_pattern(self, pattern_name: str) -> MCPServerPattern | None:
        """Get a server pattern by name"""
        if not self.patterns_config.exists():
            return None

        with open(self.patterns_config) as f:
            patterns = json.load(f)

        pattern_data = patterns.get(pattern_name)
        if pattern_data:
            return MCPServerPattern(**pattern_data)
        return None

    def add_server_config(self, config: MCPEnvironmentConfig) -> bool:
        """Add a new server configuration"""
        try:
            with open(self.servers_config) as f:
                servers_data = json.load(f)

            # Convert to dict, handling SecretStr
            config_dict = config.model_dump()
            # Convert SecretStr to string for storage
            config_dict["secure_vars"] = {
                k: v.get_secret_value() if hasattr(v, "get_secret_value") else str(v)
                for k, v in config.secure_vars.items()
            }

            servers_data["servers"][config.server_name] = config_dict

            with open(self.servers_config, "w") as f:
                json.dump(servers_data, f, indent=2)

            # Update .env file
            self._update_env_file(config)
            return True

        except Exception as e:
            print(f"❌ Failed to save server config: {e}")
            return False

    def _update_env_file(self, config: MCPEnvironmentConfig):
        """Update .env file with server environment variables"""
        env_lines = []

        # Read existing .env if it exists
        if self.env_file.exists():
            with open(self.env_file) as f:
                existing_lines = f.readlines()

            # Keep non-server-specific lines
            for line in existing_lines:
                if not line.startswith(f"{config.server_name.upper()}_"):
                    env_lines.append(line.rstrip())

        # Add server-specific environment variables
        for key, value in config.env_vars.items():
            env_lines.append(f"{config.server_name.upper()}_{key}={value}")

        for key, secret_value in config.secure_vars.items():
            secret_str = (
                secret_value.get_secret_value()
                if hasattr(secret_value, "get_secret_value")
                else str(secret_value)
            )
            env_lines.append(f"{config.server_name.upper()}_{key}={secret_str}")

        # Write updated .env
        with open(self.env_file, "w") as f:
            f.write("\n".join(env_lines) + "\n")

    def get_server_config(self, server_name: str) -> MCPEnvironmentConfig | None:
        """Get server configuration by name"""
        if not self.servers_config.exists():
            return None

        with open(self.servers_config) as f:
            servers_data = json.load(f)

        server_data = servers_data.get("servers", {}).get(server_name)
        if server_data:
            # Convert secure_vars back to SecretStr
            if "secure_vars" in server_data:
                server_data["secure_vars"] = {
                    k: SecretStr(v) for k, v in server_data["secure_vars"].items()
                }
            return MCPEnvironmentConfig(**server_data)
        return None

    def list_available_patterns(self) -> list[str]:
        """List all available server patterns"""
        if not self.patterns_config.exists():
            return []

        with open(self.patterns_config) as f:
            patterns = json.load(f)

        return list(patterns.keys())

    def list_configured_servers(self) -> list[str]:
        """List all configured servers"""
        if not self.servers_config.exists():
            return []

        with open(self.servers_config) as f:
            servers_data = json.load(f)

        return list(servers_data.get("servers", {}).keys())

    def export_claude_desktop_config(self, server_name: str) -> dict[str, Any] | None:
        """Export server config in Claude Desktop format"""
        config = self.get_server_config(server_name)
        if not config:
            return None

        claude_config = {
            "command": "npx" if config.package_name.startswith("@") else "python",
            "args": (
                ["-y", config.package_name] + config.startup_args
                if config.package_name.startswith("@")
                else ["-m", config.package_name.replace("-", "_")] + config.startup_args
            ),
        }

        # Add environment variables if any
        all_env = {**config.env_vars}
        for key, secret_val in config.secure_vars.items():
            all_env[key] = (
                secret_val.get_secret_value()
                if hasattr(secret_val, "get_secret_value")
                else str(secret_val)
            )

        if all_env:
            claude_config["env"] = all_env

        return {server_name: claude_config}

    def get_config_summary(self) -> dict[str, Any]:
        """Get summary of all configurations"""
        return {
            "config_directory": str(self.config_dir),
            "env_file": str(self.env_file),
            "available_patterns": self.list_available_patterns(),
            "configured_servers": self.list_configured_servers(),
            "files_exist": {
                "patterns": self.patterns_config.exists(),
                "servers": self.servers_config.exists(),
                "env": self.env_file.exists(),
            },
        }
