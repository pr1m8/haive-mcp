"""MCP mixin for adding Model Context Protocol capabilities to agents.

This module provides a mixin class that adds MCP functionality to any Haive agent.
The mixin handles server connections, tool discovery, resource access, and prompt
management with automatic error handling and graceful degradation.

The MCPMixin class integrates seamlessly with the Haive agent architecture,
providing:
    - Dynamic server discovery and connection management
    - Automatic tool registration with agents
    - Health monitoring and failure recovery
    - Component registry integration
    - Lazy initialization support

Examples:
    Adding MCP capabilities to a custom agent:

    .. code-block:: python

        from haive.agents.base import Agent
        from haive.mcp.mixins import MCPMixin
        from haive.mcp.config import MCPConfig

        class MyCustomAgent(MCPMixin, Agent):
            '''Agent with MCP capabilities.'''

            async def setup(self):
                await super().setup()
                # MCP tools are now available
                if self._mcp_tools:
                    print(f"Loaded {len(self._mcp_tools)} MCP tools")

        # Use the agent
        agent = MyCustomAgent(
            engine=engine,
            mcp_config=MCPConfig(enabled=True, servers={...})
        )

See Also:
    - :class:`haive.mcp.config.MCPConfig`: MCP configuration
    - :class:`haive.mcp.agents.MCPAgent`: Pre-built MCP agent
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from haive.core.registry import (
    RegistryManager,
)
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel, Field, PrivateAttr

from haive.mcp.config import MCPConfig, MCPServerConfig

# Conditional imports
try:
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MultiServerMCPClient = None
    BaseTool = None

logger = logging.getLogger(__name__)


class MCPMixin(BaseModel):
    """Mixin to add MCP (Model Context Protocol) capabilities to any agent.

    This mixin provides comprehensive MCP integration including server management,
    tool discovery, health monitoring, and graceful error handling. It can be
    mixed into any Haive agent to add MCP functionality.

    Attributes:
        mcp_config: Optional MCP configuration for server connections

    Private Attributes:
        _mcp_client: The MultiServerMCPClient instance for server communication
        _mcp_servers: Dictionary of configured MCP servers
        _mcp_tools: Dictionary of discovered tools from MCP servers
        _mcp_initialized: Flag indicating if MCP has been initialized
        _failed_servers: Set of server names that failed to connect
        _server_health: Health status tracking for each server

    Features:
        - Dynamic MCP server discovery and connection
        - Automatic tool registration with agent systems
        - Health monitoring with automatic reconnection
        - Graceful degradation when servers fail
        - Lazy initialization support
        - Resource and prompt management

    Examples:
        Creating a custom agent with MCP capabilities:

        .. code-block:: python

            from haive.agents.base import Agent
            from haive.mcp.mixins import MCPMixin
            from haive.mcp.config import MCPConfig, MCPServerConfig

            class MyMCPAgent(MCPMixin, Agent):
                '''Custom agent with MCP capabilities.'''

                async def setup(self):
                    await super().setup()
                    # Initialize MCP
                    if self.mcp_config:
                        await self.initialize_mcp()
                        print(f"Loaded {len(self._mcp_tools)} MCP tools")

            # Configure and use
            agent = MyMCPAgent(
                engine=engine,
                mcp_config=MCPConfig(
                    enabled=True,
                    servers={
                        "filesystem": MCPServerConfig(
                            name="filesystem",
                            transport="stdio",
                            command="npx",
                            args=["-y", "@modelcontextprotocol/server-filesystem"]
                        )
                    }
                )
    """

    # MCP configuration
    mcp_config: MCPConfig | None = Field(default=None)

    # Private attributes for state management
    _mcp_client: MultiServerMCPClient | None = PrivateAttr(default=None)
    _mcp_servers: dict[str, MCPServerConfig] = PrivateAttr(default_factory=dict)
    _mcp_tools: dict[str, BaseTool] = PrivateAttr(default_factory=dict)
    _mcp_initialized: bool = PrivateAttr(default=False)
    _failed_servers: set[str] = PrivateAttr(default_factory=set)
    _server_health: dict[str, dict[str, Any]] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """Initialize MCP mixin after model initialization."""
        # Call parent's model_post_init if it exists
        try:
            super().model_post_init(__context)
        except AttributeError:
            # Parent doesn't have model_post_init
            pass

        # Note: We don't auto-initialize here because we can't run async code
        # in model_post_init. Users should call initialize_mcp() or setup()

    def setup_mcp(self):
        """Setup MCP after agent initialization."""
        if self.mcp_config and self.mcp_config.enabled:
            # Register MCP tools with the agent
            if hasattr(self, "setup_tools"):
                # This will be called during agent setup
                asyncio.create_task(self._setup_mcp_tools())

    async def _setup_mcp_tools(self):
        """Setup MCP tools for the agent."""
        if (
            not self._mcp_initialized
            and self.mcp_config
            and not self.mcp_config.lazy_init
        ):
            await self.initialize_mcp()

        # Add discovered tools to agent's tools
        if self._mcp_tools:
            if hasattr(self, "tools") and isinstance(self.tools, list):
                for tool in self._mcp_tools.values():
                    if tool not in self.tools:
                        self.tools.append(tool)
            elif hasattr(self, "engine") and hasattr(self.engine, "bind_tools"):
                # Bind tools to the engine
                tools_list = list(self._mcp_tools.values())
                self.engine = self.engine.bind_tools(tools_list)

    async def initialize_mcp(self) -> bool:
        """Initialize MCP servers and client.

        Establishes connections to all configured MCP servers, discovers available
        tools, and registers them with the component registry if available.

        The initialization process:
            1. Checks for MCP dependencies availability
            2. Discovers servers if auto-discovery is enabled
            3. Connects to each configured server
            4. Creates MultiServerMCPClient with connected servers
            5. Discovers tools from all servers
            6. Registers servers and tools with component registry

        Returns:
            bool: True if at least one server connected successfully, False otherwise

        Raises:
            Exception: Logged but not raised to ensure graceful degradation

        Examples:
            Manual initialization:

            .. code-block:: python

                agent = MCPAgent(engine=engine, mcp_config=config)
                success = await agent.initialize_mcp()
                if success:
                    print(f"Connected to {len(agent._mcp_servers)} servers")
        """
        if not MCP_AVAILABLE:
            logger.warning(
                "MCP dependencies not available. Install with: pip install langchain-mcp-adapters"
            )
            return False

        if not self.mcp_config or not self.mcp_config.enabled:
            return False

        if self._mcp_initialized:
            return True

        try:
            # Discover servers if auto-discovery enabled
            if self.mcp_config.auto_discover:
                await self._discover_servers()

            # Connect to servers
            connected_servers = await self._connect_servers()

            if connected_servers:
                # Create MCP client with connected servers
                self._mcp_client = MultiServerMCPClient(connected_servers)

                # Discover tools
                await self._discover_tools()

                # Register tools with component registry if available
                await self._register_tools_with_registry()

                self._mcp_initialized = True
                logger.info(f"MCP initialized with {len(connected_servers)} servers")
                return True
            logger.warning("No MCP servers connected")
            return False

        except Exception as e:
            logger.exception(f"Failed to initialize MCP: {e}")
            return False

    async def _discover_servers(self):
        """Discover MCP servers from configured paths."""
        # TODO: Implement server discovery from files/registry
        # For now, we'll use the configured servers

    async def _connect_servers(self) -> dict[str, dict[str, Any]]:
        """Connect to configured MCP servers.

        Returns:
            Dictionary of successfully connected server configurations
        """
        connected = {}

        if not self.mcp_config:
            return connected

        for server_name, server_config in self.mcp_config.servers.items():
            if not server_config.enabled:
                continue

            if await self._test_server_connection(server_name, server_config):
                # Convert to format expected by MultiServerMCPClient
                connection_config = self._create_connection_config(server_config)
                connected[server_name] = connection_config
                self._mcp_servers[server_name] = server_config
            else:
                self._failed_servers.add(server_name)
                logger.warning(f"Failed to connect to MCP server: {server_name}")

        return connected

    async def _test_server_connection(self, name: str, config: MCPServerConfig) -> bool:
        """Test if a server is reachable."""
        try:
            # Create temporary client to test connection
            test_config = {name: self._create_connection_config(config)}
            test_client = MultiServerMCPClient(test_config)

            # Try to get tools as a connection test
            await asyncio.wait_for(
                test_client.get_tools(server_name=name), timeout=config.timeout
            )

            # Clean up test client
            if hasattr(test_client, "close"):
                await test_client.close()

            return True

        except Exception as e:
            logger.debug(f"Server {name} connection test failed: {e}")
            return False

    def _create_connection_config(
        self, server_config: MCPServerConfig
    ) -> dict[str, Any]:
        """Create connection configuration for MultiServerMCPClient."""
        config = {}

        if server_config.transport == "stdio":
            config["command"] = server_config.command
            config["args"] = server_config.args
            config["transport"] = "stdio"
        elif server_config.transport in ["sse", "streamable_http"]:
            config["url"] = server_config.url
            config["transport"] = server_config.transport

        # Add environment variables
        if server_config.env:
            config["env"] = server_config.env

        return config

    async def _discover_tools(self):
        """Discover tools from connected MCP servers."""
        if not self._mcp_client:
            return

        try:
            # Get all tools from all servers
            all_tools = await self._mcp_client.get_tools()

            # Store tools with server prefix for disambiguation
            for tool in all_tools:
                # Tools from MCP often have server prefix already
                tool_name = tool.name
                self._mcp_tools[tool_name] = tool

                # Track which server provides which tool
                server_name = tool_name.split("_")[0] if "_" in tool_name else "unknown"
                if server_name not in self._server_health:
                    self._server_health[server_name] = {"tools": []}
                self._server_health[server_name]["tools"].append(tool_name)

            logger.info(f"Discovered {len(self._mcp_tools)} MCP tools")

        except Exception as e:
            logger.exception(f"Failed to discover MCP tools: {e}")

    async def _register_tools_with_registry(self):
        """Register MCP tools with the component registry if available."""
        try:
            # Get MCP registry
            mcp_registry = RegistryManager.get_registry("mcp")
            tool_registry = RegistryManager.get_registry("tools")

            # Register each MCP server
            for server_name, server_config in self._mcp_servers.items():
                metadata = {
                    "name": server_name,
                    "component_type": "mcp",
                    "capabilities": server_config.capabilities,
                    "tags": (
                        ["mcp", server_config.category]
                        if server_config.category
                        else ["mcp"]
                    ),
                    "description": server_config.description
                    or f"MCP Server: {server_name}",
                }
                mcp_registry.register(
                    name=server_name,
                    component={"name": server_name, "config": server_config},
                    metadata=metadata,
                )

            # Register each tool
            for tool_name, tool in self._mcp_tools.items():
                server_name = tool_name.split("_")[0] if "_" in tool_name else "unknown"
                metadata = {
                    "name": tool_name,
                    "component_type": "tool",
                    "capabilities": ["mcp_tool", "remote_execution"],
                    "tags": ["mcp", f"mcp_{server_name}"],
                    "description": getattr(
                        tool, "description", f"MCP Tool: {tool_name}"
                    ),
                }
                tool_registry.register(
                    name=tool_name,
                    component=tool,
                    metadata=metadata,
                )

            logger.info(
                f"Registered {len(self._mcp_servers)} MCP servers and {len(self._mcp_tools)} tools with component registry"
            )

        except ImportError:
            # Component registry not available
            logger.debug("Component registry not available, skipping registration")
        except Exception as e:
            logger.exception(f"Failed to register with component registry: {e}")

    @asynccontextmanager
    async def mcp_session(self, server_name: str | None = None):
        """Context manager for MCP operations.

        Args:
            server_name: Optional specific server to use

        Yields:
            MCP client or session
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()

        if server_name and self._mcp_client:
            # Use specific server session
            async with self._mcp_client.session(server_name) as session:
                yield session
        else:
            # Use the general client
            yield self._mcp_client

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        server_name: str | None = None,
    ) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            server_name: Optional specific server to use

        Returns:
            Tool execution result
        """
        if not self._mcp_initialized:
            await self.initialize_mcp()

        if tool_name not in self._mcp_tools:
            raise ValueError(f"MCP tool '{tool_name}' not found")

        tool = self._mcp_tools[tool_name]

        # Execute tool
        try:
            result = await tool.ainvoke(arguments)
            return result
        except Exception as e:
            logger.exception(f"Error executing MCP tool {tool_name}: {e}")
            raise

    async def get_mcp_resources(
        self, server_name: str, uris: str | list[str] | None = None
    ) -> list[Any]:
        """Get resources from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()

        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self._mcp_client.get_resources(server_name, uris=uris)

    async def get_mcp_prompt(
        self,
        server_name: str,
        prompt_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> list[Any]:
        """Get a prompt from an MCP server."""
        if not self._mcp_initialized:
            await self.initialize_mcp()

        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")

        return await self._mcp_client.get_prompt(
            server_name, prompt_name, arguments=arguments
        )

    def get_mcp_status(self) -> dict[str, Any]:
        """Get current MCP status."""
        return {
            "enabled": self.mcp_config.enabled if self.mcp_config else False,
            "initialized": self._mcp_initialized,
            "connected_servers": list(
                set(self._mcp_servers.keys()) - self._failed_servers
            ),
            "failed_servers": list(self._failed_servers),
            "available_tools": list(self._mcp_tools.keys()),
            "tool_count": len(self._mcp_tools),
        }

    async def refresh_mcp_servers(self):
        """Refresh MCP server connections."""
        # Reset state
        self._mcp_initialized = False
        self._failed_servers.clear()
        self._mcp_tools.clear()

        # Re-initialize
        await self.initialize_mcp()

    async def cleanup_mcp(self):
        """Clean up MCP resources."""
        if self._mcp_client and hasattr(self._mcp_client, "close"):
            try:
                await self._mcp_client.close()
            except Exception as e:
                logger.exception(f"Error closing MCP client: {e}")

        self._mcp_client = None
        self._mcp_initialized = False
