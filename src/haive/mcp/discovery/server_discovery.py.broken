"""Dynamic MCP server discovery and loading system.

This module provides functionality for discovering MCP servers from various sources
including file system paths, registries, and well-known server locations. It supports
dynamic loading, filtering, and registration of servers with the component registry.

The discovery system:
    - Scans configured paths for server definitions
    - Checks for well-known MCP server packages
    - Filters servers based on capabilities and categories
    - Integrates with the Haive component registry
    - Provides detailed discovery reports

Classes:
    MCPServerDiscovery: Main class for discovering and managing MCP servers

Example:
    Basic server discovery::
    
        from haive.mcp.discovery import MCPServerDiscovery
        from haive.mcp.config import MCPConfig
        
        # Configure discovery
        config = MCPConfig(
            auto_discover=True,
            discovery_paths=["~/.mcp/servers", "./mcp_servers"],
            categories=["filesystem", "development"],
            required_capabilities=["file_read"]
        )
        
        # Discover servers
        discovery = MCPServerDiscovery(config)
        servers = await discovery.discover_all()
        
        print(f"Found {len(servers)} servers")
        
        # Get servers by capability
        db_servers = discovery.get_servers_by_capability("database")
        
        # Create config with discovered servers
        mcp_config = discovery.create_mcp_config()

Note:
    Server discovery is asynchronous and may take time depending on the
    number of paths to scan and servers to verify.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.discovery.analyzer import MCPServerAnalyzer

logger = logging.getLogger(__name__)


class MCPServerDiscovery:
    """Discovers and manages MCP servers dynamically.
    
    MCPServerDiscovery provides comprehensive server discovery capabilities,
    scanning multiple sources to find available MCP servers and creating
    configurations for them. It supports filtering, validation, and
    registration with the component system.
    
    The discovery process:
        1. Loads servers from configuration
        2. Scans discovery paths for server definitions
        3. Queries the component registry
        4. Checks for well-known server packages
        5. Applies filters based on categories and capabilities
        6. Validates server availability
    
    Attributes:
        config: MCP configuration with discovery settings
        analyzer: Server analyzer for parsing configurations
        discovered_servers: Dictionary of discovered server configurations
        _discovery_sources: Set of sources where servers were found
    
    Example:
        Discovering and filtering servers::
        
            # Create discovery with filters
            discovery = MCPServerDiscovery(
                MCPConfig(
                    auto_discover=True,
                    categories=["development", "database"],
                    required_capabilities=["repo_access"]
                )
            )
            
            # Discover all matching servers
            servers = await discovery.discover_all()
            
            # Get discovery report
            report = discovery.get_discovery_report()
            print(f"Found servers in categories: {report['categories']}")
            print(f"Available capabilities: {report['unique_capabilities']}")
    "
    
    def __init__(self, config: Optional[MCPConfig] = None):
        """Initialize MCP server discovery.
        
        Sets up the discovery system with the provided configuration or
        defaults. Creates an analyzer for parsing server definitions.
        
        Args:
            config: Optional MCP configuration with discovery settings.
                If not provided, uses default MCPConfig.
        """
        self.config = config or MCPConfig()
        self.analyzer = MCPServerAnalyzer()
        self.discovered_servers: Dict[str, MCPServerConfig] = {}
        self._discovery_sources: Set[str] = set()
    
    async def discover_all(self) -> Dict[str, MCPServerConfig]:
        """Discover all available MCP servers from configured sources.
        
        Performs comprehensive discovery across all configured sources,
        including explicit configurations, file system paths, registries,
        and well-known server locations. Applies filters to the results.
        
        The discovery process is additive - servers from all sources are
        combined, with later discoveries potentially overriding earlier
        ones if they have the same name.
        
        Returns:
            Dict[str, MCPServerConfig]: Dictionary mapping server names to
                their configurations. Only includes servers that pass all
                configured filters.
                
        Example:
            Discovering with multiple sources::
            
                config = MCPConfig(
                    servers={  # Explicit servers
                        "custom": MCPServerConfig(name="custom", ...)
                    },
                    auto_discover=True,
                    discovery_paths=["~/.mcp", "/etc/mcp"]
                )
                
                discovery = MCPServerDiscovery(config)
                all_servers = await discovery.discover_all()
                
                # Will include:
                # - The explicit "custom" server
                # - Servers found in ~/.mcp
                # - Servers found in /etc/mcp
                # - Well-known servers if available
        """
        servers = {}
        
        # Add configured servers first
        if self.config.servers:
            servers.update(self.config.servers)
        
        # Discover from paths if auto-discovery enabled
        if self.config.auto_discover:
            for path_str in self.config.discovery_paths:
                path = Path(path_str).expanduser()
                if path.exists():
                    discovered = await self._discover_from_path(path)
                    servers.update(discovered)
            
            # Discover from registry
            registry_servers = await self._discover_from_registry()
            servers.update(registry_servers)
            
            # Discover from well-known locations
            well_known = await self._discover_well_known()
            servers.update(well_known)
        
        # Apply filters
        filtered = self._apply_filters(servers)
        
        self.discovered_servers = filtered
        return filtered
    
    async def _discover_from_path(self, path: Path) -> Dict[str, MCPServerConfig]:
        """Discover servers from a directory path.
        
        Scans a path for MCP server configurations. Handles both individual
        configuration files and directories containing multiple configs.
        
        Supported formats:
            - JSON files with single server configuration
            - JSON files with array of server configurations
            - Directories containing multiple configuration files
        
        Args:
            path: Path to scan for server configurations
            
        Returns:
            Dict[str, MCPServerConfig]: Discovered server configurations
            
        Note:
            Errors during discovery are logged but don't stop the process.
            Invalid configurations are skipped.
        """
        servers = {}
        
        try:
            if path.is_dir():
                # Discover from directory
                configs = self.analyzer.discover_from_directory(path)
                for config in configs:
                    servers[config.name] = config
                    self._discovery_sources.add(str(path))
            elif path.is_file():
                # Single config file
                with open(path) as f:
                    data = json.load(f)
                
                if isinstance(data, dict):
                    config = self.analyzer.analyze(data, str(path))
                    if config:
                        servers[config.name] = config
                        self._discovery_sources.add(str(path))
                elif isinstance(data, list):
                    for item in data:
                        config = self.analyzer.analyze(item, str(path))
                        if config:
                            servers[config.name] = config
                            self._discovery_sources.add(str(path))
                            
        except Exception as e:
            logger.error(f"Failed to discover from {path}: {e}")
        
        return servers
    
    async def _discover_from_registry(self) -> Dict[str, MCPServerConfig]:
        """Discover servers from registry.
        
        Queries the component registry for registered MCP servers. This allows
        servers to be discovered that were registered by other parts of the
        system.
        
        Returns:
            Dict[str, MCPServerConfig]: Server configurations from registry
        """
        servers = {}
        
        configs = self.analyzer.discover_from_registry()
        for config in configs:
            servers[config.name] = config
            self._discovery_sources.add("registry")
        
        return servers
    
    async def _discover_well_known(self) -> Dict[str, MCPServerConfig]:
        """Discover well-known MCP servers.
        
        Checks for commonly used MCP servers that can be run via npx.
        Only includes servers that are actually available on the system.
        
        Well-known servers include:
            - filesystem: Local file system operations
            - github: GitHub repository integration
            - time: Time and date utilities
            - fetch: HTTP request capabilities
        
        Returns:
            Dict[str, MCPServerConfig]: Available well-known servers
            
        Note:
            Requires npx to be installed for server availability checks.
        """
        servers = {}
        
        # Check for installed npm packages
        well_known_servers = [
            {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "capabilities": ["file_read", "file_write", "directory_list"],
                "category": "filesystem",
                "description": "Local filesystem operations"
            },
            {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "capabilities": ["repo_access", "issue_management", "pr_operations"],
                "category": "development",
                "description": "GitHub repository operations"
            },
            {
                "name": "time",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-time"],
                "capabilities": ["time_queries", "timezone_conversion"],
                "category": "utilities",
                "description": "Time and date operations"
            },
            {
                "name": "fetch",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-fetch"],
                "capabilities": ["web_fetch", "http_requests"],
                "category": "web",
                "description": "HTTP fetch operations"
            }
        ]
        
        # Check if servers are available
        for server_info in well_known_servers:
            if await self._check_server_available(server_info):
                config = self.analyzer.analyze(server_info)
                if config:
                    servers[config.name] = config
                    self._discovery_sources.add("well_known")
        
        return servers
    
    async def _check_server_available(self, server_info: Dict[str, Any]) -> bool:
        """Check if a server command is available.
        
        Verifies that a server can be executed by checking if its command
        exists on the system. For npx-based servers, checks if npx is
        available.
        
        Args:
            server_info: Server information including command and args
            
        Returns:
            bool: True if the server command is available
        """
        try:
            # Simple check - try to run with --help
            command = server_info.get("command", "")
            args = server_info.get("args", [])
            
            if command == "npx":
                # For npx, we'll assume it's available if npx exists
                proc = await asyncio.create_subprocess_exec(
                    "npx", "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return proc.returncode == 0
            else:
                # For other commands, check if executable exists
                proc = await asyncio.create_subprocess_exec(
                    "which", command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return proc.returncode == 0
                
        except Exception:
            return False
    
    def _apply_filters(self, servers: Dict[str, MCPServerConfig]) -> Dict[str, MCPServerConfig]:
        """Apply configured filters to discovered servers.
        
        Filters servers based on:
            - Enabled status
            - Category (if categories filter is set)
            - Required capabilities (all must be present)
        
        Args:
            servers: Dictionary of all discovered servers
            
        Returns:
            Dict[str, MCPServerConfig]: Filtered server configurations
        """
        filtered = {}
        
        for name, config in servers.items():
            # Skip disabled servers
            if not config.enabled:
                continue
            
            # Filter by category
            if self.config.categories:
                if not config.category or config.category not in self.config.categories:
                    continue
            
            # Filter by required capabilities
            if self.config.required_capabilities:
                if not all(cap in config.capabilities for cap in self.config.required_capabilities):
                    continue
            
            filtered[name] = config
        
        return filtered
    
    def get_servers_by_capability(self, capability: str) -> List[MCPServerConfig]:
        """Get all servers that provide a specific capability.
        
        Searches through discovered servers to find those that include
        the specified capability in their capabilities list.
        
        Args:
            capability: The capability to search for (e.g., "file_read",
                "database_query", "repo_access")
            
        Returns:
            List[MCPServerConfig]: Server configurations that provide
                the requested capability
                
        Example:
            Finding database servers::
            
                # Discover servers first
                await discovery.discover_all()
                
                # Find all database-capable servers
                db_servers = discovery.get_servers_by_capability("database_query")
                
                for server in db_servers:
                    print(f"{server.name}: {server.description}")
        """
        return [
            config for config in self.discovered_servers.values()
            if capability in config.capabilities
        ]
    
    def get_servers_by_category(self, category: str) -> List[MCPServerConfig]:
        """Get all servers in a specific category.
        
        Filters discovered servers by their category assignment.
        
        Args:
            category: The category to filter by (e.g., "filesystem",
                "development", "database", "utilities")
            
        Returns:
            List[MCPServerConfig]: Server configurations in the
                specified category
                
        Example:
            Getting development tools::
            
                # Get all development-related servers
                dev_servers = discovery.get_servers_by_category("development")
                
                # These might include GitHub, GitLab, Jira, etc.
                for server in dev_servers:
                    print(f"{server.name}: {', '.join(server.capabilities)}")
        """
        return [
            config for config in self.discovered_servers.values()
            if config.category == category
        ]
    
    async def register_with_component_registry(self):
        """Register discovered servers with the component registry.
        
        Registers all discovered servers as MCP components in the Haive
        component registry. This makes them available for discovery by
        other parts of the system.
        
        The registration includes:
            - Server configuration as the component
            - ComponentType.MCP as the type
            - Metadata with capabilities and description
            
        Note:
            Failures to register are logged but don't raise exceptions.
            If the component registry is not available, this is a no-op.
        """
        try:
            from haive.core.utils.component_discovery import create_component_registry, ComponentType
            
            registry = create_component_registry()
            
            for server_config in self.discovered_servers.values():
                component_info = self.analyzer.create_component_info(server_config)
                
                # Register as MCP component
                registry.register_component(
                    component=server_config,
                    component_type=ComponentType.MCP,
                    metadata=component_info
                )
            
            logger.info(f"Registered {len(self.discovered_servers)} MCP servers with component registry")
            
        except ImportError:
            logger.debug("Component registry not available")
        except Exception as e:
            logger.error(f"Failed to register with component registry: {e}")
    
    def create_mcp_config(self) -> MCPConfig:
        """Create an MCPConfig with all discovered servers.
        
        Generates a complete MCP configuration containing all discovered
        servers. The resulting config has auto_discover disabled since
        discovery has already been performed.
        
        Returns:
            MCPConfig: Configuration with all discovered servers
            
        Example:
            Using discovered servers in an agent::
            
                # Discover servers
                discovery = MCPServerDiscovery()
                await discovery.discover_all()
                
                # Create config
                mcp_config = discovery.create_mcp_config()
                
                # Use in agent
                agent = MCPAgent(
                    engine=engine,
                    mcp_config=mcp_config
                )
        """
        return MCPConfig(
            enabled=True,
            servers=self.discovered_servers,
            auto_discover=False  # Already discovered
        )
    
    def get_discovery_report(self) -> Dict[str, Any]:
        """Get a report of discovery results.
        
        Generates a comprehensive report of the discovery process including
        statistics about discovered servers, their categories, capabilities,
        and sources.
        
        Returns:
            Dict[str, Any]: Discovery report containing:
                - total_servers: Number of servers discovered
                - discovery_sources: List of sources where servers were found
                - categories: Dictionary of category counts
                - unique_capabilities: List of all unique capabilities
                - servers: Dictionary of server summaries
                
        Example:
            Analyzing discovery results::
            
                report = discovery.get_discovery_report()
                
                print(f"Total servers: {report['total_servers']}")
                print(f"Sources: {', '.join(report['discovery_sources'])}")
                print("\nCategories:")
                for cat, count in report['categories'].items():
                    print(f"  {cat}: {count} servers")
                print(f"\nUnique capabilities: {len(report['unique_capabilities'])}")
        """
        categories = {}
        capabilities = set()
        
        for config in self.discovered_servers.values():
            if config.category:
                categories[config.category] = categories.get(config.category, 0) + 1
            capabilities.update(config.capabilities)
        
        return {
            "total_servers": len(self.discovered_servers),
            "discovery_sources": list(self._discovery_sources),
            "categories": categories,
            "unique_capabilities": list(capabilities),
            "servers": {
                name: {
                    "category": config.category,
                    "capabilities": config.capabilities,
                    "transport": config.transport,
                    "enabled": config.enabled
                }
                for name, config in self.discovered_servers.items()
            }
        }