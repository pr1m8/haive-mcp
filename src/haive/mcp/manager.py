"""Dynamic MCP Manager for procedural server addition.

This module provides a comprehensive system for adding MCP servers procedurally,
one by one, during runtime. It supports incremental configuration, health monitoring,
and graceful integration with existing agents.

The manager enables:
    - Step-by-step MCP server addition
    - Runtime configuration updates
    - Health monitoring and retry logic
    - Incremental capability discovery
    - Safe server removal and replacement

Classes:
    MCPManager: Main manager for dynamic MCP operations
    MCPRegistrationResult: Result of server registration
    MCPHealthStatus: Health monitoring information

Examples:
    Adding MCP servers procedurally::

        from haive.mcp.manager import MCPManager
        from haive.mcp.config import MCPServerConfig

        # Create manager
        manager = MCPManager()

        # Add servers one by one
        await manager.add_server("filesystem", MCPServerConfig(
            name="filesystem",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        ))

        await manager.add_server("github", MCPServerConfig(
            name="github",
            transport="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_TOKEN": "your_token"}
        ))

        # Get all available tools
        tools = await manager.get_all_tools()

    Health monitoring example::

        # Check server health
        health = await manager.check_server_health("filesystem")
        if health.status == MCPServerStatus.UNHEALTHY:
            await manager.reconnect_server("filesystem")

    Tool execution example::

        # Execute a tool on specific server
        result = await manager.execute_tool(
            server="filesystem",
            tool="read_file",
            params={"path": "/path/to/file.txt"}
        )
"""

import asyncio
import contextlib
import logging
import subprocess
import traceback
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp
from langchain_mcp_adapters.client import (
    MultiServerMCPClient,
    stdio_client,
)
from mcp.client.stdio import StdioServerParameters
from pydantic import BaseModel, Field, PrivateAttr

from haive.mcp.config import MCPServerConfig

logger = logging.getLogger(__name__)

# Check for MCP availability
try:
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning(
        "MCP adapters not available. Install with: pip install langchain-mcp-adapters"
    )


class MCPServerStatus(str, Enum):
    """Status of an MCP server.

    Attributes:
        PENDING: Not yet attempted to connect
        CONNECTING: Connection in progress
        CONNECTED: Successfully connected and operational
        FAILED: Connection failed with error
        DISCONNECTED: Intentionally disconnected by user
        UNHEALTHY: Connected but health check failed
    """

    PENDING = "pending"  # Not yet attempted
    CONNECTING = "connecting"  # Connection in progress
    CONNECTED = "connected"  # Successfully connected
    FAILED = "failed"  # Connection failed
    DISCONNECTED = "disconnected"  # Intentionally disconnected
    UNHEALTHY = "unhealthy"  # Connected but health check failed


class MCPRegistrationResult(BaseModel):
    """Result of MCP server registration.

    Contains the outcome of attempting to register and connect to an MCP server.

    Attributes:
        server_name: Name of the server that was registered
        success: Whether registration and connection succeeded
        status: Current status of the server connection
        error: Optional error message if registration failed
        tools_discovered: Number of tools discovered from this server
        resources_discovered: Number of resources discovered from this server
        connection_time: Time taken to establish connection in seconds
    """

    server_name: str = Field(description="Name of the server")
    success: bool = Field(description="Whether registration succeeded")
    status: MCPServerStatus = Field(description="Current server status")
    tools_count: int = Field(default=0, description="Number of tools discovered")
    tools: list[str] = Field(default_factory=list, description="List of tool names")
    error_message: str | None = Field(
        default=None, description="Error message if failed"
    )
    connection_time: float | None = Field(
        default=None, description="Connection time in seconds"
    )


class MCPHealthStatus(BaseModel):
    """Health status information for an MCP server.

    Tracks the health and performance metrics of an individual MCP server connection.

    Attributes:
        server_name: Name of the server being monitored
        status: Current operational status
        last_check: Timestamp of the most recent health check
        response_time: Latest response time in seconds (None if failed)
        consecutive_failures: Count of consecutive failed health checks
        total_requests: Total number of requests made to this server
        successful_requests: Number of successful requests
        error_details: Details of the most recent error (if any)

    Example:
        Health status after monitoring::

            status = MCPHealthStatus(
                server_name="filesystem",
                status=MCPServerStatus.CONNECTED,
                last_check=datetime.now(),
                response_time=0.125,
                consecutive_failures=0,
                total_requests=1000,
                successful_requests=998
            )
    """

    server_name: str = Field(description="Name of the server")
    status: MCPServerStatus = Field(description="Current status")
    last_check: datetime = Field(description="Last health check time")
    response_time: float | None = Field(
        default=None, description="Response time in seconds"
    )
    consecutive_failures: int = Field(
        default=0, description="Number of consecutive failures"
    )
    total_requests: int = Field(default=0, description="Total requests made")
    successful_requests: int = Field(default=0, description="Successful requests")
    error_details: str | None = Field(default=None, description="Latest error details")


class MCPManager(BaseModel):
    """Dynamic MCP manager for procedural server addition.

    Provides a high-level interface for managing MCP servers during runtime,
    allowing for incremental addition, health monitoring, and dynamic configuration
    updates without disrupting existing connections.

    The manager maintains:
        - Individual server configurations and status
        - Health monitoring for each server
        - Consolidated tool registry from all servers
        - Connection pooling and retry logic
        - Event callbacks for server state changes

    Attributes:
        enabled: Whether MCP management is enabled
        auto_health_check: Whether to automatically monitor server health
        health_check_interval: Interval between health checks in seconds
        max_retry_attempts: Maximum retry attempts for failed connections
        connection_timeout: Timeout for server connections in seconds
    """

    enabled: bool = Field(default=True, description="Whether MCP management is enabled")
    auto_health_check: bool = Field(
        default=True, description="Enable automatic health monitoring"
    )
    health_check_interval: float = Field(
        default=30.0, description="Health check interval in seconds"
    )
    max_retry_attempts: int = Field(default=3, description="Maximum retry attempts")
    connection_timeout: float = Field(
        default=10.0, description="Connection timeout in seconds"
    )

    # Private attributes for state management
    _servers: dict[str, MCPServerConfig] = PrivateAttr(default_factory=dict)
    _server_status: dict[str, MCPServerStatus] = PrivateAttr(default_factory=dict)
    _server_health: dict[str, MCPHealthStatus] = PrivateAttr(default_factory=dict)
    _server_tools: dict[str, list[str]] = PrivateAttr(default_factory=dict)
    _clients: dict[str, Any] = PrivateAttr(default_factory=dict)
    _multi_client: Any | None = PrivateAttr(default=None)
    _health_check_task: asyncio.Task | None = PrivateAttr(default=None)
    _retry_counts: dict[str, int] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context) -> None:
        """Initialize the MCP manager after model creation."""
        # Call parent's model_post_init if it exists
        with contextlib.suppress(AttributeError):
            super().model_post_init(__context)

        # Start health monitoring if enabled
        if self.enabled and self.auto_health_check:
            self._start_health_monitoring()

    def _start_health_monitoring(self) -> None:
        """Start the background health monitoring task."""
        if not self._health_check_task or self._health_check_task.done():
            self._health_check_task = asyncio.create_task(self._health_monitor_loop())

    async def _health_monitor_loop(self) -> None:
        """Background loop for health monitoring."""
        while self.enabled and self.auto_health_check:
            try:
                await self._check_all_server_health()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.exception(f"Health monitoring error: {e}")
                await asyncio.sleep(self.health_check_interval)

    async def add_server(
        self,
        server_name: str,
        config: MCPServerConfig,
        connect_immediately: bool = True,
    ) -> MCPRegistrationResult:
        """Add a new MCP server procedurally.

        Adds a single MCP server to the manager with optional immediate connection.
        This allows for step-by-step server addition during runtime without
        disrupting existing connections.

        Args:
            server_name: Unique name for the server
            config: Complete server configuration
            connect_immediately: Whether to attempt connection immediately

        Returns:
            MCPRegistrationResult: Result of the registration attempt

        Example:
            Adding a filesystem server::

                result = await manager.add_server("filesystem", MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-filesystem"]
                ))

                if result.success:
                    print(f"Added {result.tools_count} tools")
        """
        if not MCP_AVAILABLE:
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message="MCP adapters not available",
            )

        start_time = asyncio.get_event_loop().time()

        # Store server configuration
        self._servers[server_name] = config
        self._server_status[server_name] = MCPServerStatus.PENDING
        self._retry_counts[server_name] = 0

        logger.info(f"Adding MCP server: {server_name}")

        if connect_immediately:
            result = await self._connect_server(server_name, config)
            result.connection_time = asyncio.get_event_loop().time() - start_time

            # Auto-refresh tools after successful connection
            if result.success:
                await self.refresh_tools()

            return result
        return MCPRegistrationResult(
            server_name=server_name, success=True, status=MCPServerStatus.PENDING
        )

    async def _connect_server(
        self, server_name: str, config: MCPServerConfig
    ) -> MCPRegistrationResult:
        """Connect to a specific MCP server."""
        self._server_status[server_name] = MCPServerStatus.CONNECTING

        try:
            # Debug: Check config type
            logger.debug(f"Connect config type for {server_name}: {type(config)}")
            if isinstance(config, dict):
                logger.warning(
                    f"Connect config is dict, converting to MCPServerConfig for {server_name}"
                )
                config = MCPServerConfig(**config)
            # Test server connection first
            if not await self._test_server_connection(server_name, config):
                self._server_status[server_name] = MCPServerStatus.FAILED
                return MCPRegistrationResult(
                    server_name=server_name,
                    success=False,
                    status=MCPServerStatus.FAILED,
                    error_message="Server connection test failed",
                )

            # Create connection based on transport type

            if config.transport.value == "stdio":
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args or [],
                    env=config.env or {},
                    cwd=None,
                    encoding="utf-8",
                    encoding_error_handler="strict",
                )
                # Create session with stdio client
                async with stdio_client(server_params) as session:
                    return await self._handle_session_connection(
                        server_name, config, session, server_params
                    )
            elif config.transport.value == "sse":
                # For SSE, we'll need to handle differently
                raise NotImplementedError("SSE transport not yet implemented")
            else:
                raise ValueError(f"Unsupported transport: {config.transport}")

        except Exception as e:
            error_trace = traceback.format_exc()
            logger.exception(f"Failed to add server {server_name}: {e}")
            logger.debug(f"Full traceback: {error_trace}")
            self._server_status[server_name] = MCPServerStatus.FAILED
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message=str(e),
            )

    async def _handle_session_connection(
        self, server_name: str, config: MCPServerConfig, session, server_params
    ):
        """Handle successful session connection and tool discovery."""
        try:
            # Store session info (simplified for now)
            self._clients[server_name] = {
                "session": session,
                "server_params": server_params,
            }

            # Try to list available tools
            try:
                # Simple fallback tool discovery
                if hasattr(session, "list_tools"):
                    tools_result = await session.list_tools()
                    tool_names = (
                        [tool.name for tool in tools_result.tools]
                        if hasattr(tools_result, "tools")
                        else []
                    )
                else:
                    logger.debug(
                        f"Session for {server_name} does not have list_tools method"
                    )
                    tool_names = []
            except Exception as tool_error:
                logger.debug(f"Could not load tools for {server_name}: {tool_error}")
                tool_names = []

            self._server_tools[server_name] = tool_names
            self._server_status[server_name] = MCPServerStatus.CONNECTED

            # Update health status
            self._server_health[server_name] = MCPHealthStatus(
                server_name=server_name,
                status=MCPServerStatus.CONNECTED,
                last_check=datetime.now(),
                response_time=0.0,
                total_requests=1,
                successful_requests=1,
            )

            return MCPRegistrationResult(
                server_name=server_name,
                success=True,
                status=MCPServerStatus.CONNECTED,
                tools=tool_names,
                tools_count=len(tool_names),
                error_message=None,
            )

        except Exception as e:
            logger.exception(f"Error handling session for {server_name}: {e}")
            self._server_status[server_name] = MCPServerStatus.FAILED
            self._retry_counts[server_name] = self._retry_counts.get(server_name, 0) + 1

            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message=str(e),
            )

    async def _test_server_connection(
        self, server_name: str, config: MCPServerConfig
    ) -> bool:
        """Test if a server can be connected to."""
        try:
            # Debug: Check config type
            logger.debug(f"Config type for {server_name}: {type(config)}")
            if isinstance(config, dict):
                logger.warning(
                    f"Config is dict, converting to MCPServerConfig for {server_name}"
                )
                config = MCPServerConfig(**config)
            if config.transport.value == "stdio":
                # For stdio, check if command exists
                if not config.command:
                    return False

                result = subprocess.run(
                    [config.command, "--version"],
                    capture_output=True,
                    timeout=self.connection_timeout,
                    check=False,
                )
                return (
                    result.returncode == 0
                    or "not found" not in result.stderr.decode().lower()
                )
            if config.transport.value == "sse":
                # For SSE, try a simple HTTP request

                async with (
                    aiohttp.ClientSession() as session,
                    session.get(
                        config.url,
                        timeout=aiohttp.ClientTimeout(total=self.connection_timeout),
                    ) as response,
                ):
                    return response.status < 500
            return True
        except Exception as e:
            logger.debug(f"Server connection test failed for {server_name}: {e}")
            return False

    async def _discover_server_tools(self, client: Any) -> list[Any]:
        """Discover tools from a specific MCP client."""
        try:
            tools = client.get_tools()
            return tools if tools else []
        except Exception as e:
            logger.warning(f"Failed to discover tools: {e}")
            return []

    async def _rebuild_multi_client(self) -> None:
        """Rebuild the multi-server client with all connected servers."""
        connected_clients = {
            name: client
            for name, client in self._clients.items()
            if self._server_status.get(name) == MCPServerStatus.CONNECTED
        }

        if connected_clients:
            try:
                self._multi_client = MultiServerMCPClient(connected_clients)
                logger.debug(
                    f"Rebuilt multi-client with {len(connected_clients)} servers"
                )
            except Exception as e:
                logger.exception(f"Failed to rebuild multi-client: {e}")
                self._multi_client = None

    async def remove_server(self, server_name: str) -> bool:
        """Remove an MCP server from the manager.

        Args:
            server_name: Name of the server to remove

        Returns:
            bool: True if server was removed successfully
        """
        if server_name not in self._servers:
            return False

        # Close client connection if exists
        if server_name in self._clients:
            try:
                client = self._clients[server_name]
                if hasattr(client, "close"):
                    await client.close()
            except Exception as e:
                logger.warning(f"Error closing client for {server_name}: {e}")

            del self._clients[server_name]

        # Remove from all tracking dictionaries
        self._servers.pop(server_name, None)
        self._server_status.pop(server_name, None)
        self._server_health.pop(server_name, None)
        self._server_tools.pop(server_name, None)
        self._retry_counts.pop(server_name, None)

        # Rebuild multi-client
        await self._rebuild_multi_client()

        logger.info(f"Removed MCP server: {server_name}")
        return True

    async def get_all_tools(self, refresh: bool = False) -> list[Any]:
        """Get all tools from all connected servers.

        Args:
            refresh: Whether to refresh the tool list from servers

        Returns:
            List[Any]: List of all available tools
        """
        if refresh:
            await self.refresh_tools()

        if not self._multi_client:
            return []

        try:
            return self._multi_client.get_tools() or []
        except Exception as e:
            logger.exception(f"Failed to get tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool from any connected server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            Any: Result of the tool call
        """
        if not self._multi_client:
            raise ValueError("No MCP servers connected")

        # Find tool in available tools
        tools = await self.get_all_tools()
        tool = next((t for t in tools if t.name == tool_name), None)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        return await tool.ainvoke(arguments)

    def get_server_status(self, server_name: str) -> MCPServerStatus | None:
        """Get the status of a specific server.

        Args:
            server_name: Name of the server

        Returns:
            Optional[MCPServerStatus]: Server status or None if not found
        """
        return self._server_status.get(server_name)

    def get_all_server_status(self) -> dict[str, dict[str, Any]]:
        """Get status information for all servers.

        Returns:
            Dict[str, Dict[str, Any]]: Status information for all servers
        """
        return {
            "servers": {
                name: {
                    "status": status.value,
                    "tools": self._server_tools.get(name, []),
                    "health": (
                        self._server_health[name].dict()
                        if name in self._server_health
                        and self._server_health[name] is not None
                        else None
                    ),
                }
                for name, status in self._server_status.items()
            },
            "summary": {
                "total_servers": len(self._servers),
                "connected_servers": len(
                    [
                        s
                        for s in self._server_status.values()
                        if s == MCPServerStatus.CONNECTED
                    ]
                ),
                "failed_servers": len(
                    [
                        s
                        for s in self._server_status.values()
                        if s == MCPServerStatus.FAILED
                    ]
                ),
                "total_tools": sum(len(tools) for tools in self._server_tools.values()),
            },
        }

    async def _check_all_server_health(self) -> None:
        """Check health of all connected servers."""
        for server_name, status in self._server_status.items():
            if status == MCPServerStatus.CONNECTED:
                await self._check_server_health(server_name)

    async def _check_server_health(self, server_name: str) -> None:
        """Check health of a specific server."""
        if server_name not in self._clients:
            return

        start_time = asyncio.get_event_loop().time()
        health_info = self._server_health.get(server_name)

        if not health_info:
            health_info = MCPHealthStatus(
                server_name=server_name,
                status=MCPServerStatus.CONNECTED,
                last_check=datetime.now(),
            )

        try:
            # Simple health check - try to get tools
            client = self._clients[server_name]
            await self._discover_server_tools(client)

            response_time = asyncio.get_event_loop().time() - start_time

            # Update health info
            health_info.last_check = datetime.now()
            health_info.response_time = response_time
            health_info.total_requests += 1
            health_info.successful_requests += 1
            health_info.consecutive_failures = 0
            health_info.status = MCPServerStatus.CONNECTED

        except Exception as e:
            health_info.consecutive_failures += 1
            health_info.total_requests += 1
            health_info.error_details = str(e)
            health_info.last_check = datetime.now()

            if health_info.consecutive_failures >= 3:
                health_info.status = MCPServerStatus.UNHEALTHY
                self._server_status[server_name] = MCPServerStatus.UNHEALTHY

        self._server_health[server_name] = health_info

    async def retry_failed_servers(self) -> list[MCPRegistrationResult]:
        """Retry connection to all failed servers.

        Returns:
            List[MCPRegistrationResult]: Results of retry attempts
        """
        results = []

        for server_name, status in self._server_status.items():
            if status == MCPServerStatus.FAILED:
                retry_count = self._retry_counts.get(server_name, 0)
                if retry_count < self.max_retry_attempts:
                    config = self._servers[server_name]
                    result = await self._connect_server(server_name, config)
                    results.append(result)

        return results

    async def shutdown(self) -> None:
        """Shutdown the MCP manager and close all connections."""
        self.enabled = False

        # Cancel health monitoring
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._health_check_task

        # Close all client connections
        for server_name, client in self._clients.items():
            try:
                if hasattr(client, "close"):
                    await client.close()
            except Exception as e:
                logger.warning(f"Error closing client {server_name}: {e}")

        # Clear all state
        self._clients.clear()
        self._multi_client = None

        logger.info("MCP manager shutdown complete")

    async def refresh_tools(self) -> None:
        """Refresh the tool list from all connected servers.

        This method rebuilds the multi-client and forces a fresh discovery
        of all tools from connected servers. Call this after adding new
        servers or when tools may have changed.
        """
        logger.info("Refreshing MCP tools from all connected servers")

        # Clear cached tool lists
        self._server_tools.clear()

        # Rediscover tools from each connected server
        for server_name, client_info in self._clients.items():
            if self._server_status.get(server_name) == MCPServerStatus.CONNECTED:
                try:
                    session = client_info.get("session")
                    if session and hasattr(session, "list_tools"):
                        tools_result = await session.list_tools()
                        tool_names = (
                            [tool.name for tool in tools_result.tools]
                            if hasattr(tools_result, "tools")
                            else []
                        )
                        self._server_tools[server_name] = tool_names
                        logger.debug(
                            f"Refreshed {len(tool_names)} tools from {server_name}"
                        )
                except Exception as e:
                    logger.exception(f"Failed to refresh tools from {server_name}: {e}")

        # Rebuild multi-client with fresh tool registry
        await self._rebuild_multi_client()

        logger.info(
            f"Tool refresh complete. Total tools: {sum(len(tools) for tools in self._server_tools.values())}"
        )

    async def get_resources(self, server_name: str | None = None) -> list[Any]:
        """Get available resources from MCP servers.

        Args:
            server_name: Optional specific server to query, otherwise gets from all

        Returns:
            List of available resources
        """
        resources = []

        servers_to_check = (
            [server_name]
            if server_name and server_name in self._clients
            else list(self._clients.keys())
        )

        for name in servers_to_check:
            if self._server_status.get(name) == MCPServerStatus.CONNECTED:
                try:
                    session = self._clients[name].get("session")
                    if session and hasattr(session, "list_resources"):
                        resources_result = await session.list_resources()
                        if hasattr(resources_result, "resources"):
                            resources.extend(resources_result.resources)
                except Exception as e:
                    logger.debug(f"Could not get resources from {name}: {e}")

        return resources

    async def get_prompts(self, server_name: str | None = None) -> list[Any]:
        """Get available prompts from MCP servers.

        Args:
            server_name: Optional specific server to query, otherwise gets from all

        Returns:
            List of available prompts
        """
        prompts = []

        servers_to_check = (
            [server_name]
            if server_name and server_name in self._clients
            else list(self._clients.keys())
        )

        for name in servers_to_check:
            if self._server_status.get(name) == MCPServerStatus.CONNECTED:
                try:
                    session = self._clients[name].get("session")
                    if session and hasattr(session, "list_prompts"):
                        prompts_result = await session.list_prompts()
                        if hasattr(prompts_result, "prompts"):
                            prompts.extend(prompts_result.prompts)
                except Exception as e:
                    logger.debug(f"Could not get prompts from {name}: {e}")

        return prompts

    async def reload_server(self, server_name: str) -> MCPRegistrationResult:
        """Reload a specific MCP server.

        Disconnects and reconnects to the server, refreshing all tools,
        resources, and prompts.

        Args:
            server_name: Name of the server to reload

        Returns:
            MCPRegistrationResult: Result of the reload operation
        """
        if server_name not in self._servers:
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message=f"Server {server_name} not found",
            )

        logger.info(f"Reloading MCP server: {server_name}")

        # Get the configuration
        config = self._servers[server_name]

        # Remove the server (disconnects it)
        await self.remove_server(server_name)

        # Re-add the server
        result = await self.add_server(server_name, config, connect_immediately=True)

        # Refresh tools if successful
        if result.success:
            await self.refresh_tools()

        return result
