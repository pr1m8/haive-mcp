"""Agent integration for MCP Downloader.

This module provides integration between the MCP downloader system and Haive agents,
enabling automatic tool, resource, and prompt discovery from downloaded MCP servers.

Example:
    Basic integration::

        from haive.mcp.downloader import MCPAgentIntegration

        integration = MCPAgentIntegration()
        agent = await integration.create_agent_with_mcp_servers(
            engine=engine,
            server_names=["filesystem", "github"]
        )

    Auto-discovery integration::

        agent = await integration.create_agent_with_auto_discovery(
            engine=engine,
            limit=10,
            categories=["official", "core"]
        )

Classes:
    MCPAgentIntegration: Main integration class
    MCPServerConnection: Connection management for MCP servers
    MCPCapabilityExtractor: Extract tools, resources, and prompts
"""

import logging
from pathlib import Path
from typing import Any

from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import (
    SSEConnection,
    StdioServerParameters,
    stdio_client,
)
from pydantic import BaseModel, Field

from haive.mcp.agents import MCPAgent, TransferableMCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig
from haive.mcp.downloader.config import ServerConfig
from haive.mcp.downloader.core import GeneralMCPDownloader
from haive.mcp.manager import MCPManager

logger = logging.getLogger(__name__)


class MCPServerConnection(BaseModel):
    """Manages connection to an MCP server.

    Attributes:
        name: Server name identifier
        config: Server configuration
        transport: Transport type (stdio, sse, etc.)
        connection: Active connection object
        tools: Discovered tools from the server
        resources: Available resources
        prompts: Available prompts
        connected: Connection status

    Example:
        Creating a connection::

            connection = MCPServerConnection(
                name="filesystem",
                config=server_config,
                transport="stdio"
            )
            await connection.connect()
    """

    name: str = Field(..., description="Server name")
    config: dict[str, Any] = Field(..., description="Server configuration")
    transport: str = Field(..., description="Transport type")
    connection: Any | None = Field(None, description="Connection object")
    tools: dict[str, BaseTool] = Field(
        default_factory=dict, description="Discovered tools"
    )
    resources: list[dict[str, Any]] = Field(
        default_factory=list, description="Resources"
    )
    prompts: list[dict[str, Any]] = Field(default_factory=list, description="Prompts")
    connected: bool = Field(default=False, description="Connection status")

    class Config:
        arbitrary_types_allowed = True

    async def connect(self) -> bool:
        """Establish connection to the MCP server.

        Returns:
            bool: True if connection successful

        Example:
            Connecting to server::

                if await connection.connect():
                    print(f"Connected to {connection.name}")
        """
        try:
            if self.transport == "stdio":
                # Create stdio connection
                server_params = StdioServerParameters(
                    command=self.config.get("command", "npx"),
                    args=self.config.get("args", []),
                    env=self.config.get("env", {}),
                )

                self.connection = await stdio_client(
                    server_params, self.config.get("timeout", 30)
                )

            elif self.transport == "sse":
                # Create SSE connection
                self.connection = SSEConnection(
                    url=self.config.get("url"), headers=self.config.get("headers", {})
                )
                await self.connection.connect()

            else:
                logger.warning(f"Unsupported transport: {self.transport}")
                return False

            self.connected = True
            logger.info(f"Connected to MCP server: {self.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            self.connected = False
            return False

    async def discover_capabilities(self) -> dict[str, Any]:
        """Discover tools, resources, and prompts from the server.

        Returns:
            Dict containing discovered capabilities

        Example:
            Discovering capabilities::

                caps = await connection.discover_capabilities()
                print(f"Found {len(caps['tools'])} tools")
        """
        if not self.connected or not self.connection:
            await self.connect()

        capabilities = {"tools": {}, "resources": [], "prompts": []}

        try:
            # Discover tools
            if hasattr(self.connection, "list_tools"):
                tools = await self.connection.list_tools()
                for tool in tools:
                    tool_name = f"{self.name}_{tool.name}"
                    self.tools[tool_name] = tool
                    capabilities["tools"][tool_name] = tool

            # Discover resources
            if hasattr(self.connection, "list_resources"):
                resources = await self.connection.list_resources()
                self.resources = resources
                capabilities["resources"] = resources

            # Discover prompts
            if hasattr(self.connection, "list_prompts"):
                prompts = await self.connection.list_prompts()
                self.prompts = prompts
                capabilities["prompts"] = prompts

        except Exception as e:
            logger.error(f"Error discovering capabilities for {self.name}: {e}")

        return capabilities


class MCPCapabilityExtractor:
    """Extracts tools, resources, and prompts from MCP servers.

    This class provides methods to extract and organize capabilities
    from multiple MCP servers for use with agents.

    Attributes:
        connections: Active server connections
        all_tools: Aggregated tools from all servers
        all_resources: Aggregated resources
        all_prompts: Aggregated prompts

    Example:
        Extracting capabilities::

            extractor = MCPCapabilityExtractor()
            await extractor.add_server("filesystem", config)
            tools = extractor.get_all_tools()
    """

    def __init__(self):
        """Initialize the capability extractor."""
        self.connections: dict[str, MCPServerConnection] = {}
        self.all_tools: dict[str, BaseTool] = {}
        self.all_resources: dict[str, list[dict]] = {}
        self.all_prompts: dict[str, list[dict]] = {}

    async def add_server(
        self, name: str, config: dict[str, Any], transport: str = "stdio"
    ) -> bool:
        """Add and connect to an MCP server.

        Args:
            name: Server name
            config: Server configuration
            transport: Transport type

        Returns:
            bool: True if server added successfully

        Example:
            Adding a server::

                success = await extractor.add_server(
                    "filesystem",
                    {"command": "npx", "args": ["@modelcontextprotocol/server-filesystem"]}
                )
        """
        connection = MCPServerConnection(name=name, config=config, transport=transport)

        if await connection.connect():
            self.connections[name] = connection

            # Discover and aggregate capabilities
            caps = await connection.discover_capabilities()

            # Add tools
            for tool_name, tool in caps["tools"].items():
                self.all_tools[tool_name] = tool

            # Add resources
            if caps["resources"]:
                self.all_resources[name] = caps["resources"]

            # Add prompts
            if caps["prompts"]:
                self.all_prompts[name] = caps["prompts"]

            logger.info(f"Added server {name} with {len(caps['tools'])} tools")
            return True

        return False

    async def add_servers_from_config(
        self, servers: list[ServerConfig], config_dir: Path
    ) -> dict[str, bool]:
        """Add multiple servers from configuration.

        Args:
            servers: List of server configurations
            config_dir: Directory containing server configs

        Returns:
            Dict mapping server names to success status

        Example:
            Adding from config::

                results = await extractor.add_servers_from_config(
                    downloader.servers,
                    downloader.install_dir
                )
        """
        results = {}

        for server in servers:
            if not server.enabled:
                continue

            # Load server configuration
            config_file = config_dir / "mcp_servers_config.json"
            if config_file.exists():
                import json

                with open(config_file) as f:
                    mcp_configs = json.load(f).get("mcpServers", {})

                if server.name in mcp_configs:
                    config = mcp_configs[server.name]
                    success = await self.add_server(
                        server.name,
                        config,
                        "stdio",  # Default to stdio
                    )
                    results[server.name] = success

        return results

    def get_all_tools(self) -> dict[str, BaseTool]:
        """Get all discovered tools.

        Returns:
            Dict of tool name to tool object

        Example:
            Getting tools::

                tools = extractor.get_all_tools()
                for name, tool in tools.items():
                    print(f"Tool: {name}")
        """
        return self.all_tools.copy()

    def get_all_resources(self) -> dict[str, list[dict]]:
        """Get all discovered resources.

        Returns:
            Dict of server name to resource list
        """
        return self.all_resources.copy()

    def get_all_prompts(self) -> dict[str, list[dict]]:
        """Get all discovered prompts.

        Returns:
            Dict of server name to prompt list
        """
        return self.all_prompts.copy()

    def get_tools_by_server(self, server_name: str) -> dict[str, BaseTool]:
        """Get tools from a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Dict of tools from that server
        """
        return {
            name: tool
            for name, tool in self.all_tools.items()
            if name.startswith(f"{server_name}_")
        }

    def get_tools_by_capability(self, capability: str) -> dict[str, BaseTool]:
        """Get tools that have a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            Dict of tools with that capability
        """
        matching_tools = {}
        for name, tool in self.all_tools.items():
            if hasattr(tool, "capabilities") and capability in tool.capabilities:
                matching_tools[name] = tool
        return matching_tools


class MCPAgentIntegration:
    """Integration between MCP downloader and Haive agents.

    This class provides high-level methods to create agents with
    MCP servers automatically configured and connected.

    Attributes:
        downloader: General MCP downloader instance
        extractor: Capability extractor
        manager: MCP manager for agent integration

    Example:
        Creating integrated agent::

            integration = MCPAgentIntegration()
            agent = await integration.create_agent_with_mcp_servers(
                engine=engine,
                server_names=["filesystem", "github"]
            )
    """

    def __init__(self, config_file: str | None = None, install_dir: str | None = None):
        """Initialize MCP agent integration.

        Args:
            config_file: Path to configuration file
            install_dir: Installation directory
        """
        self.downloader = GeneralMCPDownloader(config_file, install_dir)
        self.extractor = MCPCapabilityExtractor()
        self.manager = MCPManager()

    async def create_agent_with_mcp_servers(
        self,
        engine: AugLLMConfig,
        server_names: list[str],
        agent_class: type = MCPAgent,
        install_if_missing: bool = True,
        **agent_kwargs,
    ) -> MCPAgent:
        """Create an agent with specific MCP servers.

        Args:
            engine: Haive engine configuration
            server_names: List of server names to use
            agent_class: Agent class to instantiate
            install_if_missing: Install missing servers
            **agent_kwargs: Additional agent arguments

        Returns:
            Configured agent with MCP servers

        Example:
            Creating agent with servers::

                agent = await integration.create_agent_with_mcp_servers(
                    engine=engine,
                    server_names=["filesystem", "github", "postgres"],
                    name="my_mcp_agent"
                )
        """
        # Check which servers need installation
        installed_servers = self._get_installed_servers()
        missing_servers = [s for s in server_names if s not in installed_servers]

        if missing_servers and install_if_missing:
            logger.info(f"Installing missing servers: {missing_servers}")
            result = await self.downloader.download_servers(missing_servers)
            if result["failed"] > 0:
                logger.warning(
                    f"Failed to install some servers: {result['failed_servers']}"
                )

        # Add servers to extractor
        await self.extractor.add_servers_from_config(
            [s for s in self.downloader.servers if s.name in server_names],
            self.downloader.install_dir,
        )

        # Create MCP configuration
        mcp_config = self._create_mcp_config_from_extractor()

        # Create agent
        agent = agent_class(engine=engine, mcp_config=mcp_config, **agent_kwargs)

        # Initialize MCP
        await agent.setup()

        # Log summary
        tools = self.extractor.get_all_tools()
        resources = self.extractor.get_all_resources()
        prompts = self.extractor.get_all_prompts()

        logger.info(
            f"Created agent with {len(tools)} tools, "
            f"{sum(len(r) for r in resources.values())} resources, "
            f"{sum(len(p) for p in prompts.values())} prompts"
        )

        return agent

    async def create_agent_with_auto_discovery(
        self,
        engine: AugLLMConfig,
        limit: int | None = None,
        categories: list[str] | None = None,
        tags: set[str] | None = None,
        agent_class: type = MCPAgent,
        **agent_kwargs,
    ) -> MCPAgent:
        """Create an agent with auto-discovered MCP servers.

        Args:
            engine: Haive engine configuration
            limit: Maximum servers to discover
            categories: Server categories to include
            tags: Server tags to filter by
            agent_class: Agent class to instantiate
            **agent_kwargs: Additional agent arguments

        Returns:
            Configured agent with discovered servers

        Example:
            Auto-discovery agent::

                agent = await integration.create_agent_with_auto_discovery(
                    engine=engine,
                    limit=10,
                    categories=["official", "core"],
                    tags={"file-operations", "database"}
                )
        """
        # Auto-discover and install servers
        logger.info("Auto-discovering MCP servers...")
        await self.downloader.auto_discover_and_download(limit=limit)

        # Filter by categories and tags
        selected_servers = []
        for server in self.downloader.servers:
            if categories:
                template = self.downloader.templates.get(server.template)
                if not template or template.category not in categories:
                    continue

            if tags and not server.tags.intersection(tags):
                continue

            selected_servers.append(server.name)

        # Create agent with selected servers
        return await self.create_agent_with_mcp_servers(
            engine=engine,
            server_names=selected_servers,
            agent_class=agent_class,
            install_if_missing=False,  # Already installed
            **agent_kwargs,
        )

    async def create_transferable_agent_team(
        self,
        engine: AugLLMConfig,
        num_agents: int,
        server_distribution: str = "shared",
        **agent_kwargs,
    ) -> list[TransferableMCPAgent]:
        """Create a team of transferable MCP agents.

        Args:
            engine: Haive engine configuration
            num_agents: Number of agents to create
            server_distribution: How to distribute servers
                - "shared": All agents share all servers
                - "split": Divide servers among agents
                - "specialized": Each agent gets specific categories
            **agent_kwargs: Additional agent arguments

        Returns:
            List of configured transferable agents

        Example:
            Creating agent team::

                agents = await integration.create_transferable_agent_team(
                    engine=engine,
                    num_agents=3,
                    server_distribution="specialized"
                )
        """
        # Get all available servers
        all_servers = [s.name for s in self.downloader.servers if s.enabled]

        agents = []

        if server_distribution == "shared":
            # All agents get all servers
            for i in range(num_agents):
                agent = await self.create_agent_with_mcp_servers(
                    engine=engine,
                    server_names=all_servers,
                    agent_class=TransferableMCPAgent,
                    name=f"agent_{i}",
                    **agent_kwargs,
                )
                agents.append(agent)

        elif server_distribution == "split":
            # Divide servers among agents
            servers_per_agent = len(all_servers) // num_agents
            for i in range(num_agents):
                start_idx = i * servers_per_agent
                end_idx = start_idx + servers_per_agent
                if i == num_agents - 1:
                    end_idx = len(all_servers)

                agent_servers = all_servers[start_idx:end_idx]
                agent = await self.create_agent_with_mcp_servers(
                    engine=engine,
                    server_names=agent_servers,
                    agent_class=TransferableMCPAgent,
                    name=f"agent_{i}",
                    **agent_kwargs,
                )
                agents.append(agent)

        elif server_distribution == "specialized":
            # Each agent gets servers from specific categories
            categories = list(
                set(
                    self.downloader.templates[s.template].category
                    for s in self.downloader.servers
                    if s.enabled and s.template in self.downloader.templates
                )
            )

            for i in range(num_agents):
                category = categories[i % len(categories)]
                category_servers = [
                    s.name
                    for s in self.downloader.servers
                    if s.enabled
                    and s.template in self.downloader.templates
                    and self.downloader.templates[s.template].category == category
                ]

                agent = await self.create_agent_with_mcp_servers(
                    engine=engine,
                    server_names=category_servers,
                    agent_class=TransferableMCPAgent,
                    name=f"{category}_specialist_{i}",
                    **agent_kwargs,
                )
                agents.append(agent)

        return agents

    def get_capability_summary(self) -> dict[str, Any]:
        """Get a summary of all discovered capabilities.

        Returns:
            Dict with capability statistics

        Example:
            Getting summary::

                summary = integration.get_capability_summary()
                print(f"Total tools: {summary['total_tools']}")
        """
        tools = self.extractor.get_all_tools()
        resources = self.extractor.get_all_resources()
        prompts = self.extractor.get_all_prompts()

        return {
            "total_tools": len(tools),
            "total_resources": sum(len(r) for r in resources.values()),
            "total_prompts": sum(len(p) for p in prompts.values()),
            "servers": list(self.extractor.connections.keys()),
            "tools_by_servef": {
                server: len(self.extractor.get_tools_by_server(server))
                for server in self.extractor.connections
            },
            "resources_by_servef": {
                server: len(res) for server, res in resources.items()
            },
            "prompts_by_servef": {server: len(prm) for server, prm in prompts.items()},
        }

    def _get_installed_servers(self) -> set[str]:
        """Get list of installed servers.

        Returns:
            Set of installed server names
        """
        config_file = self.downloader.install_dir / "mcp_servers_config.json"
        if config_file.exists():
            import json

            with open(config_file) as f:
                config = json.load(f)
                return set(config.get("mcpServers", {}).keys())
        return set()

    def _create_mcp_config_from_extractor(self) -> MCPConfig:
        """Create MCP configuration from extractor data.

        Returns:
            MCPConfig object for agent initialization
        """
        servers = {}

        for name, connection in self.extractor.connections.items():
            servers[name] = MCPServerConfig(
                name=name,
                transport=connection.transport,
                command=connection.config.get("command"),
                args=connection.config.get("args", []),
                url=connection.config.get("url"),
                env=connection.config.get("env", {}),
                capabilities=list(connection.tools.keys()),
            )

        return MCPConfig(
            enabled=True, servers=servers, auto_discover=False, lazy_init=False
        )
