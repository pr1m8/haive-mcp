"""Configuration models for MCP Downloader.

This module defines the configuration models used throughout the MCP downloader
system, including templates, server configurations, and installation methods.

Example:
    Creating a server template::

        template = ServerTemplate(
            name="npm_official",
            installation_method=InstallationMethod.NPM,
            command_pattern="@modelcontextprotocol/server-{service}",
            capabilities=["tools"],
            category="official"
        )

    Creating a server configuration::

        config = ServerConfig(
            name="filesystem",
            template="npm_official",
            source="npm",
            variables={"service": "filesystem"},
            tags={"official", "file-operations"}
        )

Classes:
    InstallationMethod: Enum of supported installation methods
    ServerTemplate: Template for server installation patterns
    ServerConfig: Configuration for a specific server
    DownloaderConfig: Overall downloader configuration
"""

from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class InstallationMethod(str, Enum):
    """Supported installation methods for MCP servers.

    Attributes:
        NPM: Node Package Manager installation
        PIP: Python Package Index installation
        GIT: Git repository cloning
        DOCKER: Docker image pull
        BINARY: Binary executable download
        CURL: Direct HTTP download
        MANUAL: Manual installation process
        SCRIPT: Custom script execution
    """

    NPM = "npm"
    PIP = "pip"
    GIT = "git"
    DOCKER = "docker"
    BINARY = "binary"
    CURL = "curl"
    MANUAL = "manual"
    SCRIPT = "script"


class ServerTemplate(BaseModel):
    """Template for MCP server installation patterns.

    Templates define reusable installation patterns that can be applied
    to multiple servers with similar installation requirements.

    Attributes:
        name: Unique template identifier
        installation_method: Method to use for installation
        command_pattern: Pattern for the command to run the server
        args_pattern: Default arguments for the command
        env_vars: Environment variables to set
        capabilities: List of server capabilities
        category: Server category for organization
        health_check: Command to verify server health
        prerequisites: Required system dependencies
        post_install: Commands to run after installation
        timeout: Installation timeout in seconds

    Example:
        NPM template::

            template = ServerTemplate(
                name="npm_official",
                installation_method=InstallationMethod.NPM,
                command_pattern="@modelcontextprotocol/server-{service}",
                capabilities=["tools"],
                category="official",
                prerequisites=["node", "npm"]
            )
    """

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., description="Unique template identifier")
    installation_method: InstallationMethod = Field(
        ..., description="Installation method"
    )
    command_pattern: str = Field(..., description="Command pattern with variables")
    args_pattern: list[str] = Field(
        default_factory=list, description="Default arguments"
    )
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Server capabilities"
    )
    category: str = Field(default="general", description="Server category")
    health_check: str | None = Field(None, description="Health check command")
    prerequisites: list[str] = Field(
        default_factory=list, description="System prerequisites"
    )
    post_install: list[str] = Field(
        default_factory=list, description="Post-install commands"
    )
    timeout: int = Field(default=300, description="Installation timeout in seconds")


class ServerConfig(BaseModel):
    """Configuration for a specific MCP server.

    Server configurations define individual servers to be installed,
    referencing a template and providing server-specific variables.

    Attributes:
        name: Server name identifier
        template: Template name to use
        source: Source location (npm, git URL, etc.)
        variables: Variables to substitute in template patterns
        enabled: Whether the server is enabled for installation
        priority: Installation priority (lower = higher priority)
        tags: Set of tags for categorization
        env_vars: Additional environment variables
        version: Specific version to install

    Example:
        Filesystem server config::

            config = ServerConfig(
                name="filesystem",
                template="npm_official",
                source="npm",
                variables={"service": "filesystem"},
                tags={"official", "file-operations"},
                priority=1
            )
    """

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., description="Server name identifier")
    template: str = Field(..., description="Template name to use")
    source: str = Field(..., description="Source location")
    variables: dict[str, Any] = Field(
        default_factory=dict, description="Template variables"
    )
    enabled: bool = Field(default=True, description="Enable server for installation")
    priority: int = Field(default=0, description="Installation priority")
    tags: set[str] = Field(default_factory=set, description="Server tags")
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Additional env vars"
    )
    version: str | None = Field(None, description="Specific version constraint")


class DiscoveryConfig(BaseModel):
    """Configuration for server discovery.

    Attributes:
        sources: List of discovery source URLs
        patterns: Package naming patterns by registry
        auto_discover: Enable automatic discovery
        discovery_interval: Hours between discovery runs
        max_servers: Maximum servers to discover per source
    """

    sources: list[str] = Field(
        default_factory=list, description="Discovery source URLs"
    )
    patterns: dict[str, list[str]] = Field(
        default_factory=dict, description="Naming patterns"
    )
    auto_discover: bool = Field(default=False, description="Enable auto-discovery")
    discovery_interval: int = Field(default=24, description="Hours between discovery")
    max_servers: int = Field(default=100, description="Max servers per source")


class DownloaderConfig(BaseModel):
    """Overall configuration for the MCP downloader.

    Attributes:
        install_dir: Directory for server installations
        config_dir: Directory for configuration files
        log_dir: Directory for log files
        max_concurrent: Maximum concurrent downloads
        retry_attempts: Number of retry attempts
        retry_delay: Delay between retries in seconds
        health_check_enabled: Enable health checks after install
        health_check_timeout: Health check timeout in seconds
        backup_enabled: Enable configuration backups
        backup_dir: Directory for backups
        templates: List of server templates
        servers: List of server configurations
        discovery: Discovery configuration

    Example:
        Full configuration::

            config = DownloaderConfig(
                install_dir="/home/user/.mcp/servers",
                max_concurrent=5,
                retry_attempts=3,
                templates=[template1, template2],
                servers=[server1, server2]
            )
    """

    install_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp" / "servers",
        description="Installation directory",
    )
    config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp" / "configs",
        description="Configuration directory",
    )
    log_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp" / "logs",
        description="Log directory",
    )
    max_concurrent: int = Field(default=5, gt=0, description="Max concurrent downloads")
    retry_attempts: int = Field(default=3, ge=0, description="Retry attempts")
    retry_delay: int = Field(default=5, gt=0, description="Retry delay in seconds")
    health_check_enabled: bool = Field(default=True, description="Enable health checks")
    health_check_timeout: int = Field(
        default=30, gt=0, description="Health check timeout"
    )
    backup_enabled: bool = Field(default=True, description="Enable backups")
    backup_dir: Path = Field(
        default_factory=lambda: Path.home() / ".mcp" / "backups",
        description="Backup directory",
    )
    templates: list[ServerTemplate] = Field(
        default_factory=list, description="Server templates"
    )
    servers: list[ServerConfig] = Field(
        default_factory=list, description="Server configs"
    )
    discovery: DiscoveryConfig = Field(
        default_factory=DiscoveryConfig, description="Discovery config"
    )


def load_config(config_file: Path) -> DownloaderConfig:
    """Load configuration from YAML file.

    Args:
        config_file: Path to YAML configuration file

    Returns:
        DownloaderConfig: Loaded configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid

    Example:
        Loading config::

            config = load_config(Path("mcp_config.yaml"))
            print(f"Loaded {len(config.templates)} templates")
    """

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    try:
        with open(config_file) as f:
            data = yaml.safe_load(f)

        # Convert template data
        templates = []
        for template_data in data.get("templates", []):
            templates.append(ServerTemplate(**template_data))

        # Convert server data
        servers = []
        for server_data in data.get("servers", []):
            servers.append(ServerConfig(**server_data))

        # Create config
        config_data = data.copy()
        config_data["templates"] = templates
        config_data["servers"] = servers

        return DownloaderConfig(**config_data)

    except Exception as e:
        raise ValueError(f"Invalid config file: {e}")


def save_config(config: DownloaderConfig, config_file: Path) -> None:
    """Save configuration to YAML file.

    Args:
        config: Configuration to save
        config_file: Path to save file

    Example:
        Saving config::

            config = DownloaderConfig(max_concurrent=10)
            save_config(config, Path("my_config.yaml"))
    """

    # Convert to dict for YAML serialization
    data = config.model_dump(mode="json")

    # Ensure directories exist
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
