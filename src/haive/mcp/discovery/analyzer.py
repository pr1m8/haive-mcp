"""MCP server analyzer for component discovery integration.

This module provides analysis capabilities for discovering and configuring MCP
servers from various sources. It can analyze dictionaries, objects, and files
to extract valid MCP server configurations.

The analyzer supports:
    - Dictionary-based configurations (JSON/YAML)
    - Object attribute extraction
    - Directory scanning for config files
    - Registry file parsing
    - Component info generation for discovery system

Classes:
    MCPServerAnalyzer: Main analyzer for MCP server discovery

Example:
    Analyzing server configurations:

    .. code-block:: python

        from haive.mcp.discovery import MCPServerAnalyzer

        analyzer = MCPServerAnalyzer()

        # Analyze a dictionary config
        config_dict = {
            "name": "my_server",
            "command": "npx",
            "args": ["-y", "@myorg/mcp-server"],
            "capabilities": ["data_access"]
        }

        server_config = analyzer.analyze(config_dict)
        if server_config:
            print(f"Found server: {server_config.name}")

        # Discover from directory
        configs = analyzer.discover_from_directory(Path("./mcp_configs"))
        print(f"Discovered {len(configs)} servers")

Note:
    The analyzer is designed to be flexible and handle various configuration
    formats commonly used for MCP servers.
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from haive.mcp.config import MCPServerConfig, MCPTransport

logger = logging.getLogger(__name__)


class MCPServerAnalyzer:
    """Analyzer for discovering and analyzing MCP servers.

    MCPServerAnalyzer provides comprehensive analysis capabilities for
    MCP server configurations. It can identify MCP servers from various
    sources and convert them to standardized MCPServerConfig instances.

    The analyzer integrates with haive-core's component discovery system
    to automatically find and register MCP servers. It supports multiple
    configuration formats and can extract server information from objects,
    dictionaries, and files.

    Attributes:
        discovered_servers: Dictionary of servers found during analysis

    Example:
        Basic server analysis:

        .. code-block:: python

            analyzer = MCPServerAnalyzer()

            # Check if object can be analyzed
            if analyzer.can_analyze(my_object):
                config = analyzer.analyze(my_object)
                if config:
                    print(f"Server: {config.name}")
                    print(f"Transport: {config.transport}")
                    print(f"Capabilities: {config.capabilities}")
    """

    def __init__(self):
        """Initialize the MCP server analyzer.

        Sets up the analyzer with an empty dictionary to track
        discovered servers during analysis operations.
        """
        self.discovered_servers: dict[str, MCPServerConfig] = {}

    def can_analyze(self, obj: Any) -> bool:
        """Check if an object is an MCP server or configuration.

        Determines whether an object appears to be an MCP server or
        configuration by checking for characteristic attributes and
        patterns.

        Detection criteria:
            - Dictionary with MCP config keys (command, url, transport)
            - Class name containing "MCPServer" or "MCP"
            - Object with MCP-related attributes

        Args:
            obj: Object to check for MCP characteristics

        Returns:
            bool: True if the object appears to be MCP-related

        Example:
            Checking various objects:

            .. code-block:: python

                # Dictionary config
                config = {"command": "npx", "args": [...]}
                assert analyzer.can_analyze(config) == True

                # Non-MCP object
                assert analyzer.can_analyze({"foo": "bar"}) == False

                # MCP server instance
                server = MCPServer(...)
                assert analyzer.can_analyze(server) == True
        """
        # Check for MCP server characteristics
        if isinstance(obj, dict):
            # MCP server config pattern
            return any(key in obj for key in ["command", "url", "transport"])

        # Check for MCP server class
        if hasattr(obj, "__class__"):
            class_name = obj.__class__.__name__
            return "MCPServer" in class_name or "MCP" in class_name

        return False

    def analyze(self, obj: Any, source: str | None = None) -> MCPServerConfig | None:
        """Analyze an object and extract MCP server configuration.

        Attempts to extract a valid MCPServerConfig from various object
        types. Supports dictionaries, MCPServerConfig instances, objects
        with conversion methods, and arbitrary objects with MCP attributes.

        Args:
            obj: Object to analyze. Can be:
                - Dictionary with MCP configuration
                - MCPServerConfig instance
                - Object with to_mcp_config() method
                - Any object with MCP-related attributes
            source: Optional source identifier (file path, registry key, etc.)
                Used for naming and debugging.

        Returns:
            Optional[MCPServerConfig]: Extracted configuration if successful,
                None if the object cannot be converted to a valid config.

        Example:
            Analyzing different object types::

                # From dictionary
                config = analyzer.analyze({
                    "name": "test",
                    "command": "test-server",
                    "capabilities": ["test"]
                })

                # From custom object
                class MyServer:
                    def to_mcp_config(self):
                        return MCPServerConfig(name="custom", ...)

                server = MyServer()
                config = analyzer.analyze(server)
        """
        try:
            if isinstance(obj, dict):
                return self._analyze_dict_config(obj, source)
            if isinstance(obj, MCPServerConfig):
                return obj
            if hasattr(obj, "to_mcp_config"):
                # Custom MCP server with conversion method
                return obj.to_mcp_config()
            # Try to extract config from object attributes
            return self._analyze_object(obj, source)
        except Exception as e:
            logger.exception(f"Failed to analyze MCP server: {e}")
            return None

    def _analyze_dict_config(
        self, config: dict[str, Any], source: str | None = None
    ) -> MCPServerConfig | None:
        """Analyze a dictionary configuration.

        Extracts MCP server configuration from a dictionary, determining
        the transport type and building a complete MCPServerConfig.

        Transport detection:
            - "command" present -> stdio transport
            - "url" present -> SSE or specified transport
            - Neither -> Invalid configuration

        Args:
            config: Dictionary containing server configuration
            source: Optional source identifier for naming

        Returns:
            Optional[MCPServerConfig]: Valid configuration or None

        Note:
            Missing names are generated from source or defaulted.
            All optional fields use sensible defaults.
        """
        try:
            # Determine transport type
            if "command" in config:
                transport = MCPTransport.STDIO
            elif "url" in config:
                transport = config.get("transport", MCPTransport.SSE)
            else:
                return None

            # Extract name
            name = config.get("name")
            if not name and source:
                # Generate name from source
                name = Path(source).stem.replace("-", "_").replace(" ", "_")
            if not name:
                name = "unnamed_mcp_server"

            # Build server config
            server_config = MCPServerConfig(
                name=name,
                transport=transport,
                command=config.get("command"),
                args=config.get("args", []),
                url=config.get("url"),
                env=config.get("env", {}),
                api_key=config.get("api_key"),
                category=config.get("category"),
                description=config.get("description"),
                capabilities=config.get("capabilities", []),
                timeout=config.get("timeout", 30),
                retry_attempts=config.get("retry_attempts", 3),
                auto_start=config.get("auto_start", True),
                health_check_interval=config.get("health_check_interval"),
            )

            return server_config

        except Exception as e:
            logger.exception(f"Failed to analyze dict config: {e}")
            return None

    def _analyze_object(
        self, obj: Any, source: str | None = None
    ) -> MCPServerConfig | None:
        """Analyze an arbitrary object for MCP server configuration.

        Attempts to extract MCP configuration by examining object attributes.
        Uses a mapping of common attribute names to find relevant data.

        Attribute mappings:
            - command: "command", "cmd", "executable"
            - args: "args", "arguments", "params"
            - url: "url", "endpoint", "server_url"
            - name: "name", "id", "identifier"
            - transport: "transport", "protocol"
            - capabilities: "capabilities", "features", "supported_operations"

        Args:
            obj: Object to analyze for MCP attributes
            source: Optional source identifier

        Returns:
            Optional[MCPServerConfig]: Extracted configuration or None
        """
        try:
            # Try to extract configuration attributes
            config = {}

            # Common attribute names
            attr_mapping = {
                "command": ["command", "cmd", "executable"],
                "args": ["args", "arguments", "params"],
                "url": ["url", "endpoint", "server_url"],
                "name": ["name", "id", "identifier"],
                "transport": ["transport", "protocol"],
                "capabilities": ["capabilities", "features", "supported_operations"],
            }

            for target, possible_attrs in attr_mapping.items():
                for attr in possible_attrs:
                    if hasattr(obj, attr):
                        value = getattr(obj, attr)
                        if value is not None:
                            config[target] = value
                            break

            if config:
                return self._analyze_dict_config(config, source)

            return None

        except Exception as e:
            logger.exception(f"Failed to analyze object: {e}")
            return None

    def discover_from_directory(self, directory: Path) -> list[MCPServerConfig]:
        """Discover MCP server configurations from a directory.

        Recursively searches a directory for MCP server configuration files.
        Supports JSON and YAML formats (if PyYAML is available).

        File patterns:
            - **/*.json: JSON configuration files
            - **/*.yaml: YAML configuration files (requires PyYAML)

        Configuration formats:
            - Single server: {"command": "...", "capabilities": [...]}
            - Multiple servers: [{...}, {...}, ...]

        Args:
            directory: Directory path to search recursively

        Returns:
            List[MCPServerConfig]: All valid configurations found

        Example:
            Discovering from a config directory::

                configs_dir = Path("~/.mcp/configs").expanduser()
                servers = analyzer.discover_from_directory(configs_dir)

                for server in servers:
                    print(f"Found: {server.name} ({server.transport})")

        Note:
            Invalid files are skipped with debug logging.
            YAML support is optional and fails gracefully.
        """
        discovered = []

        # Look for JSON config files
        for config_file in directory.glob("**/*.json"):
            try:
                with open(config_file) as f:
                    data = json.load(f)

                # Check if it's an MCP config
                if isinstance(data, dict) and self.can_analyze(data):
                    config = self.analyze(data, str(config_file))
                    if config:
                        discovered.append(config)
                elif isinstance(data, list):
                    # List of configs
                    for item in data:
                        if self.can_analyze(item):
                            config = self.analyze(item, str(config_file))
                            if config:
                                discovered.append(config)

            except Exception as e:
                logger.debug(f"Failed to read {config_file}: {e}")

        # Look for YAML config files
        try:
            for config_file in directory.glob("**/*.yaml"):
                try:
                    with open(config_file) as f:
                        data = yaml.safe_load(f)

                    if isinstance(data, dict) and self.can_analyze(data):
                        config = self.analyze(data, str(config_file))
                        if config:
                            discovered.append(config)

                except Exception as e:
                    logger.debug(f"Failed to read {config_file}: {e}")

        except ImportError:
            # YAML not available
            pass

        return discovered

    def discover_from_registry(
        self, registry_path: Path | None = None
    ) -> list[MCPServerConfig]:
        """Discover MCP servers from a registry file.

        Loads MCP server configurations from a JSON registry file. If no
        path is provided, checks standard registry locations.

        Registry format:
            {
                "servers": {
                    "server_name": {
                        "command": "...",
                        "capabilities": [...]
                    }
                }
            }

        Default locations checked:
            1. ~/.mcp/registry.json
            2. ~/.config/mcp/servers.json
            3. /etc/mcp/servers.json

        Args:
            registry_path: Optional path to registry file. If not provided,
                searches default locations.

        Returns:
            List[MCPServerConfig]: Configurations from the registry

        Example:
            Using a custom registry::

                # Load from specific registry
                servers = analyzer.discover_from_registry(
                    Path("/opt/mcp/registry.json")
                )

                # Use default locations
                servers = analyzer.discover_from_registry()
        """
        if not registry_path:
            # Check default locations
            possible_paths = [
                Path.home() / ".mcp" / "registry.json",
                Path.home() / ".config" / "mcp" / "servers.json",
                Path("/etc/mcp/servers.json"),
            ]

            for path in possible_paths:
                if path.exists():
                    registry_path = path
                    break

        if not registry_path or not registry_path.exists():
            return []

        discovered = []

        try:
            with open(registry_path) as f:
                registry = json.load(f)

            if isinstance(registry, dict):
                # Registry format: {"servers": {...}}
                servers = registry.get("servers", registry)

                for server_name, server_config in servers.items():
                    if isinstance(server_config, dict):
                        server_config["name"] = server_name
                        config = self.analyze(server_config, str(registry_path))
                        if config:
                            discovered.append(config)

        except Exception as e:
            logger.exception(f"Failed to read registry: {e}")

        return discovered

    def create_component_info(self, server_config: MCPServerConfig) -> dict[str, Any]:
        """Create component info for registration with component discovery."""
        return {
            "name": server_config.name,
            "component_type": "mcp",
            "capabilities": server_config.capabilities,
            "capability_categories": ["integration"],
            "tags": (
                ["mcp", server_config.category] if server_config.category else ["mcp"]
            ),
            "description": server_config.description
            or f"MCP Server: {server_config.name}",
            "config": server_config.dict(),
            "transport": server_config.transport,
            "enabled": server_config.enabled,
        }
