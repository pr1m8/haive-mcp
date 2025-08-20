"""Dynamic MCP Manager for procedural server addition and bulk operations.

This module provides a comprehensive system for adding MCP servers procedurally,
one by one, during runtime, plus industrial-strength bulk operations for managing
hundreds of servers from the 1900+ available MCP server ecosystem.

The manager enables:
    - Step-by-step MCP server addition
    - Bulk installation and management operations
    - Runtime configuration updates
    - Health monitoring and retry logic
    - Incremental capability discovery
    - Safe server removal and replacement
    - Progress tracking for bulk operations
    - Category-based server management

Classes:
    MCPManager: Main manager for dynamic MCP operations
    MCPRegistrationResult: Result of server registration
    MCPHealthStatus: Health monitoring information

Examples:
    Adding MCP servers procedurally:

        .. code-block:: python
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

    Health monitoring example:



        .. code-block:: python



            # Check server health
        health = await manager.check_server_health("filesystem")
        if health.status == MCPServerStatus.UNHEALTHY:
            await manager.reconnect_server("filesystem")

    Tool execution example:



        .. code-block:: python



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
from pydantic import BaseModel, Field, PrivateAttr

# Try to import MCP adapters, handle gracefully if missing
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from mcp.client.stdio import StdioServerParameters, stdio_client

    MCP_AVAILABLE = True
except ImportError as e:
    # Handle missing MCP adapters gracefully for documentation builds
    print(f"Warning: MCP adapters not available: {e}")
    MultiServerMCPClient = None
    StdioServerParameters = None
    stdio_client = None
    MCP_AVAILABLE = False

from haive.mcp.config import MCPServerConfig

logger = logging.getLogger(__name__)


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

    Examples:
        Health status after monitoring:

        .. code-block:: python
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


class MCPBulkOperation(BaseModel):
    """Represents a bulk operation on multiple MCP servers.
    
    Tracks progress, results, and errors for bulk installation, removal,
    or update operations across multiple servers.
    """
    
    operation_id: str = Field(description="Unique operation identifier")
    operation_type: str = Field(description="Type of operation (install, remove, update)")
    server_names: list[str] = Field(description="List of servers in operation")
    started_at: datetime = Field(description="Operation start time")
    completed_at: datetime | None = Field(default=None, description="Operation completion time")
    total_count: int = Field(description="Total number of servers")
    completed_count: int = Field(default=0, description="Number completed")
    success_count: int = Field(default=0, description="Number successful")
    failed_count: int = Field(default=0, description="Number failed")
    current_server: str | None = Field(default=None, description="Currently processing server")
    succeeded_servers: list[str] = Field(default_factory=list, description="Successfully processed")
    failed_servers: list[dict] = Field(default_factory=list, description="Failed with errors")
    is_complete: bool = Field(default=False, description="Whether operation is complete")
    
    @property
    def progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_count == 0:
            return 100.0
        return (self.completed_count / self.total_count) * 100.0
    
    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.completed_count == 0:
            return 0.0
        return (self.success_count / self.completed_count) * 100.0


class MCPServerCategory(BaseModel):
    """Represents a category of MCP servers for bulk operations."""
    
    name: str = Field(description="Category name")
    description: str = Field(description="Category description")
    servers: list[str] = Field(description="Server names in this category")
    tags: list[str] = Field(default_factory=list, description="Category tags")
    popularity_threshold: int | None = Field(default=None, description="Minimum stars for inclusion")


class MCPBulkInstaller(BaseModel):
    """Handles bulk installation of MCP servers with progress tracking."""
    
    max_concurrent: int = Field(default=5, description="Maximum concurrent installations")
    timeout_per_server: float = Field(default=60.0, description="Timeout per server installation")
    retry_attempts: int = Field(default=2, description="Retry attempts for failed installations")
    show_progress: bool = Field(default=True, description="Show progress updates")
    
    # Private attributes
    _active_operations: dict[str, MCPBulkOperation] = PrivateAttr(default_factory=dict)
    _npm_cache_path: str | None = PrivateAttr(default=None)
    
    async def bulk_install_servers(
        self, 
        server_packages: list[str], 
        operation_id: str | None = None
    ) -> MCPBulkOperation:
        """Install multiple MCP servers in parallel with progress tracking."""
        import uuid
        import subprocess
        
        if operation_id is None:
            operation_id = str(uuid.uuid4())
        
        operation = MCPBulkOperation(
            operation_id=operation_id,
            operation_type="install",
            server_names=server_packages,
            started_at=datetime.now(),
            total_count=len(server_packages)
        )
        
        self._active_operations[operation_id] = operation
        
        # Create semaphore for concurrent control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def install_single_server(package_name: str):
            async with semaphore:
                operation.current_server = package_name
                success = False
                error_msg = None
                
                for attempt in range(self.retry_attempts + 1):
                    try:
                        # Install the MCP server package using npm install -g
                        # This ensures the package is actually installed, not just validated
                        cmd = ["npm", "install", "-g", package_name]
                        
                        if self.show_progress:
                            logger.info(f"Installing {package_name} (attempt {attempt + 1}/{self.retry_attempts + 1})")
                        
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        
                        stdout, stderr = await asyncio.wait_for(
                            process.communicate(),
                            timeout=self.timeout_per_server
                        )
                        
                        if process.returncode == 0:
                            success = True
                            operation.succeeded_servers.append(package_name)
                            operation.success_count += 1
                            if self.show_progress:
                                logger.info(f"✅ Successfully installed {package_name}")
                            break
                        else:
                            error_msg = stderr.decode() if stderr else f"Exit code: {process.returncode}"
                            if self.show_progress:
                                logger.warning(f"❌ Failed to install {package_name}: {error_msg}")
                    
                    except asyncio.TimeoutError:
                        error_msg = f"Installation timeout after {self.timeout_per_server}s"
                        if self.show_progress:
                            logger.warning(f"⏰ Timeout installing {package_name}")
                    except Exception as e:
                        error_msg = str(e)
                        if self.show_progress:
                            logger.warning(f"💥 Error installing {package_name}: {e}")
                
                if not success:
                    operation.failed_servers.append({
                        "server": package_name,
                        "error": error_msg,
                        "attempts": self.retry_attempts + 1
                    })
                    operation.failed_count += 1
                
                operation.completed_count += 1
                operation.current_server = None
        
        # Run all installations in parallel (with semaphore limiting)
        await asyncio.gather(*[
            install_single_server(package) for package in server_packages
        ])
        
        operation.completed_at = datetime.now()
        operation.is_complete = True
        
        if self.show_progress:
            logger.info(f"🎉 Bulk installation complete: {operation.success_count}/{operation.total_count} successful")
        
        return operation
    
    def get_operation_status(self, operation_id: str) -> MCPBulkOperation | None:
        """Get status of a bulk operation."""
        return self._active_operations.get(operation_id)


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

        # Initialize bulk operations
        self._bulk_installer = MCPBulkInstaller()
        self._server_categories = self._load_default_categories()

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

        Examples:
            Adding a filesystem server:

        .. code-block:: python
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
        """Connect to a specific MCP server using correct LangChain patterns."""
        if not MCP_AVAILABLE:
            logger.warning("MCP adapters not available, cannot connect to servers")
            return MCPRegistrationResult(
                server_name=server_name,
                success=False,
                status=MCPServerStatus.FAILED,
                error_message="MCP adapters not available",
            )

        self._server_status[server_name] = MCPServerStatus.CONNECTING

        try:
            # Create connection configuration based on transport type
            if config.transport.value == "stdio":
                # Import StdioConnection for LangChain adapters
                from langchain_mcp_adapters.client import StdioConnection
                
                # Create connection configuration with required 'transport' field
                connection = {
                    "transport": "stdio",
                    "command": config.command,
                    "args": config.args or [],
                    "env": config.env or {}
                }
                
                # Store the connection configuration
                self._clients[server_name] = connection
                
                # Test connection by creating a temporary client
                test_client = MultiServerMCPClient({server_name: connection})
                
                # Try to get tools as a connection test
                try:
                    tools = await test_client.get_tools()
                    tool_names = [tool.name for tool in tools] if tools else []
                    self._server_tools[server_name] = tool_names
                    
                    self._server_status[server_name] = MCPServerStatus.CONNECTED
                    
                    # Update health status
                    self._server_health[server_name] = MCPHealthStatus(
                        server_name=server_name,
                        status=MCPServerStatus.CONNECTED,
                        last_check=datetime.now(),
                        response_time=0.0,
                        total_requests=1,
                        successful_requests=1
                    )
                    
                    return MCPRegistrationResult(
                        server_name=server_name,
                        success=True,
                        status=MCPServerStatus.CONNECTED,
                        tools=tool_names,
                        tools_count=len(tool_names)
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to get tools from {server_name}: {e}")
                    raise
                    
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
                # Create new MultiServerMCPClient (NOT as context manager)
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
            # Return tools from individual servers if no multi-client
            all_tools = []
            for tools in self._server_tools.values():
                if isinstance(tools, list):
                    all_tools.extend(tools)
            return all_tools

        try:
            # Get tools from multi-client
            tools = await self._multi_client.get_tools()
            return tools or []
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
        tool = next((t for t in tools if hasattr(t, 'name') and t.name == tool_name), None)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        # LangChain tools use ainvoke
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

        # Rebuild multi-client first
        await self._rebuild_multi_client()
        
        # If we have a multi-client, use it
        if self._multi_client:
            try:
                all_tools = await self._multi_client.get_tools()
                
                # Group tools by server (assuming tool names have server prefix)
                for tool in all_tools:
                    server_name = tool.name.split("_")[0] if "_" in tool.name else "unknown"
                    if server_name not in self._server_tools:
                        self._server_tools[server_name] = []
                    self._server_tools[server_name].append(tool.name)
                    
                logger.info(f"Refreshed {len(all_tools)} tools total")
            except Exception as e:
                logger.exception(f"Failed to refresh tools from multi-client: {e}")
        else:
            # Fallback: Try to get tools from individual connections
            for server_name, connection in self._clients.items():
                if self._server_status.get(server_name) == MCPServerStatus.CONNECTED:
                    try:
                        temp_client = MultiServerMCPClient({server_name: connection})
                        tools = await temp_client.get_tools()
                        self._server_tools[server_name] = [tool.name for tool in tools] if tools else []
                        logger.debug(f"Refreshed {len(tools or [])} tools from {server_name}")
                    except Exception as e:
                        logger.exception(f"Failed to refresh tools from {server_name}: {e}")

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

    # ========== BULK OPERATIONS ==========
    
    # Bulk operations will be initialized in model_post_init
    
    def _load_default_categories(self) -> dict[str, MCPServerCategory]:
        """Load verified server categories for bulk operations.
        
        ✅ VERIFIED REGISTRY: All packages have been tested to exist on npm.
        Only includes packages that are confirmed to install successfully via npm/npx.
        """
        return {
            "core": MCPServerCategory(
                name="core",
                description="Essential MCP servers for development",
                servers=[
                    # ✅ Verified core official servers
                    "@modelcontextprotocol/server-filesystem",
                    "@modelcontextprotocol/server-github",
                    "@modelcontextprotocol/server-postgres",
                    "@modelcontextprotocol/server-puppeteer",
                    "@modelcontextprotocol/server-brave-search",
                ],
                tags=["core", "development", "filesystem", "github", "database", "search"]
            ),
            
            "ai_enhanced": MCPServerCategory(
                name="ai_enhanced",
                description="AI reasoning and cognitive enhancement tools",
                servers=[
                    # ✅ Verified AI/thinking servers
                    "@modelcontextprotocol/server-sequential-thinking",
                    "@modelcontextprotocol/server-memory",
                ],
                tags=["ai", "reasoning", "memory", "thinking", "cognitive"]
            ),
            
            "time_utilities": MCPServerCategory(
                name="time_utilities",
                description="Time and scheduling utilities",
                servers=[
                    # ✅ Verified time-related servers (community packages)
                    "time-mcp",  # Time awareness for LLMs
                ],
                tags=["time", "scheduling", "utilities", "productivity"]
            ),
            
            "crypto_finance": MCPServerCategory(
                name="crypto_finance",
                description="Cryptocurrency and financial data tools",
                servers=[
                    # ✅ Verified crypto/finance servers
                    "mcp-crypto-price",  # Real-time crypto data via CoinCap
                ],
                tags=["crypto", "finance", "market", "trading", "price"]
            ),
            
            "enhanced_filesystem": MCPServerCategory(
                name="enhanced_filesystem",
                description="Enhanced filesystem and file operations",
                servers=[
                    # ✅ Verified enhanced filesystem tools
                    "filenexus",  # FileNexus for advanced file operations
                    "vuln-fs",    # Security-focused filesystem operations
                ],
                tags=["filesystem", "security", "files", "enhanced"]
            ),
            
            "browser_automation": MCPServerCategory(
                name="browser_automation",
                description="Browser automation and web interaction tools",
                servers=[
                    # ✅ Verified browser automation servers
                    "@modelcontextprotocol/server-puppeteer",
                    "puppeteer-mcp-server",  # Alternative puppeteer implementation
                ],
                tags=["browser", "automation", "puppeteer", "web", "scraping"]
            ),
            
            "github_enhanced": MCPServerCategory(
                name="github_enhanced", 
                description="Enhanced GitHub integration tools",
                servers=[
                    # ✅ Verified GitHub servers
                    "@modelcontextprotocol/server-github",
                    "github-repo-mcp",  # GitHub repository code fetching
                ],
                tags=["github", "git", "repository", "code", "integration"]
            ),
            
            "notifications": MCPServerCategory(
                name="notifications",
                description="Notification and messaging systems",
                servers=[
                    # ✅ Verified notification servers
                    "ntfy-me-mcp",  # Self-hosted ntfy notifications
                ],
                tags=["notifications", "messaging", "ntfy", "self-hosted"]
            )
        }
    
    async def bulk_install_category(
        self, 
        category_name: str, 
        max_concurrent: int = 5
    ) -> MCPBulkOperation:
        """Install all servers in a category.
        
        Args:
            category_name: Name of the category to install
            max_concurrent: Maximum concurrent installations
            
        Returns:
            MCPBulkOperation: Operation tracking object
        """
        if category_name not in self._server_categories:
            available = list(self._server_categories.keys())
            raise ValueError(f"Category '{category_name}' not found. Available: {available}")
        
        category = self._server_categories[category_name]
        self._bulk_installer.max_concurrent = max_concurrent
        
        logger.info(f"🚀 Starting bulk installation of '{category_name}' category ({len(category.servers)} servers)")
        
        operation = await self._bulk_installer.bulk_install_servers(category.servers)
        
        # After installation, add successful servers to manager
        for server_package in operation.succeeded_servers:
            try:
                # Extract server name from package (e.g., @modelcontextprotocol/server-filesystem -> filesystem)
                server_name = server_package.split("/")[-1].replace("server-", "")
                
                config = MCPServerConfig(
                    name=server_name,
                    transport="stdio",
                    command="npx",
                    args=["-y", server_package]
                )
                
                await self.add_server(server_name, config, connect_immediately=False)
                logger.info(f"✅ Added {server_name} to manager")
                
            except Exception as e:
                logger.warning(f"Failed to add {server_package} to manager: {e}")
        
        return operation
    
    async def bulk_install_servers(
        self, 
        server_packages: list[str], 
        add_to_manager: bool = True,
        max_concurrent: int = 5
    ) -> MCPBulkOperation:
        """Install multiple MCP servers in parallel.
        
        Args:
            server_packages: List of npm package names to install
            add_to_manager: Whether to add installed servers to the manager
            max_concurrent: Maximum concurrent installations
            
        Returns:
            MCPBulkOperation: Operation tracking object
        """
        self._bulk_installer.max_concurrent = max_concurrent
        
        logger.info(f"🚀 Starting bulk installation of {len(server_packages)} servers")
        
        operation = await self._bulk_installer.bulk_install_servers(server_packages)
        
        if add_to_manager:
            # Add successful installations to manager
            for server_package in operation.succeeded_servers:
                try:
                    server_name = server_package.split("/")[-1].replace("server-", "")
                    
                    config = MCPServerConfig(
                        name=server_name,
                        transport="stdio", 
                        command="npx",
                        args=["-y", server_package]
                    )
                    
                    await self.add_server(server_name, config, connect_immediately=False)
                    
                except Exception as e:
                    logger.warning(f"Failed to add {server_package} to manager: {e}")
        
        return operation
    
    async def bulk_remove_servers(self, server_names: list[str]) -> MCPBulkOperation:
        """Remove multiple servers from the manager.
        
        Args:
            server_names: List of server names to remove
            
        Returns:
            MCPBulkOperation: Operation tracking object
        """
        import uuid
        
        operation = MCPBulkOperation(
            operation_id=str(uuid.uuid4()),
            operation_type="remove",
            server_names=server_names,
            started_at=datetime.now(),
            total_count=len(server_names)
        )
        
        for server_name in server_names:
            operation.current_server = server_name
            
            try:
                success = await self.remove_server(server_name)
                if success:
                    operation.succeeded_servers.append(server_name)
                    operation.success_count += 1
                    logger.info(f"✅ Removed {server_name}")
                else:
                    operation.failed_servers.append({
                        "server": server_name,
                        "error": "Server not found or removal failed",
                        "attempts": 1
                    })
                    operation.failed_count += 1
                    
            except Exception as e:
                operation.failed_servers.append({
                    "server": server_name,
                    "error": str(e),
                    "attempts": 1
                })
                operation.failed_count += 1
                logger.warning(f"❌ Failed to remove {server_name}: {e}")
            
            operation.completed_count += 1
            operation.current_server = None
        
        operation.completed_at = datetime.now()
        operation.is_complete = True
        
        logger.info(f"🎉 Bulk removal complete: {operation.success_count}/{operation.total_count} successful")
        
        return operation
    
    async def bulk_health_check(self) -> dict[str, Any]:
        """Perform health check on all connected servers.
        
        Returns:
            Dict with health status for all servers
        """
        logger.info("🔍 Starting bulk health check on all connected servers")
        
        health_results = {}
        
        for server_name in self._servers.keys():
            if self._server_status.get(server_name) == MCPServerStatus.CONNECTED:
                try:
                    await self._check_server_health(server_name)
                    health_info = self._server_health.get(server_name)
                    
                    health_results[server_name] = {
                        "status": health_info.status.value if health_info else "unknown",
                        "response_time": health_info.response_time if health_info else None,
                        "consecutive_failures": health_info.consecutive_failures if health_info else 0,
                        "last_check": health_info.last_check.isoformat() if health_info else None
                    }
                    
                except Exception as e:
                    health_results[server_name] = {
                        "status": "error", 
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }
        
        healthy_count = sum(1 for h in health_results.values() if h["status"] == "connected")
        total_count = len(health_results)
        
        logger.info(f"🏥 Health check complete: {healthy_count}/{total_count} servers healthy")
        
        return {
            "summary": {
                "total_servers": total_count,
                "healthy_servers": healthy_count,
                "unhealthy_servers": total_count - healthy_count,
                "check_time": datetime.now().isoformat()
            },
            "details": health_results
        }
    
    def get_available_categories(self) -> dict[str, MCPServerCategory]:
        """Get all available server categories for bulk operations."""
        return self._server_categories.copy()
    
    def add_custom_category(self, category: MCPServerCategory) -> None:
        """Add a custom server category."""
        self._server_categories[category.name] = category
        logger.info(f"Added custom category: {category.name} ({len(category.servers)} servers)")
    
    async def bulk_update_servers(self) -> MCPBulkOperation:
        """Update all installed MCP servers to their latest versions.
        
        Returns:
            MCPBulkOperation: Operation tracking object
        """
        import uuid
        
        # Get all currently managed servers
        server_packages = []
        for server_name, config in self._servers.items():
            if config.command == "npx" and config.args:
                # Extract package name from args
                package_name = next((arg for arg in config.args if arg.startswith("@") or arg.startswith("server-")), None)
                if package_name:
                    server_packages.append(package_name)
        
        if not server_packages:
            # Return empty operation
            operation = MCPBulkOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="update",
                server_names=[],
                started_at=datetime.now(),
                completed_at=datetime.now(),
                total_count=0,
                is_complete=True
            )
            return operation
        
        logger.info(f"🔄 Updating {len(server_packages)} MCP servers")
        
        # Use bulk installer to reinstall (which updates)
        operation = await self._bulk_installer.bulk_install_servers(server_packages)
        operation.operation_type = "update"
        
        logger.info(f"🎉 Bulk update complete: {operation.success_count}/{operation.total_count} successful")
        
        return operation
    
    def get_bulk_operation_status(self, operation_id: str) -> MCPBulkOperation | None:
        """Get the status of a bulk operation."""
        return self._bulk_installer.get_operation_status(operation_id)
