"""MCP Client Main Implementation.

This module provides the main MCPClient class that orchestrates the MCP
protocol communication. It combines the transport layer, protocol layer,
and provides a high-level interface for MCP operations.

The client handles:
    - Connection management and lifecycle
    - Tool discovery and execution
    - Resource access and management
    - Prompt retrieval and execution
    - Server capability discovery
    - Error handling and recovery
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable, Awaitable

from .transport import MCPTransport, StdioTransport, HttpTransport
from .protocol import MCPProtocol, MCPTool, MCPPrompt, MCPResource, MCPCapability
from .exceptions import (
    MCPError,
    MCPConnectionError,
    MCPProtocolError,
    MCPToolError,
    MCPCapabilityError
)

logger = logging.getLogger(__name__)


class MCPClient:
    """High-level MCP client for communicating with MCP servers.
    
    This is the main interface for interacting with MCP servers. It combines
    the transport and protocol layers to provide a clean, easy-to-use API
    for MCP operations.
    
    The client handles the complete MCP lifecycle:
        1. Connection establishment
        2. Capability negotiation  
        3. Tool/resource/prompt discovery
        4. Operation execution
        5. Connection cleanup
        
    It supports multiple transport types and provides both sync-style
    and async context manager interfaces.
    
    Examples:
        Basic usage with STDIO transport::
        
            from haive.mcp.client import MCPClient, StdioTransport
            
            transport = StdioTransport("npx", ["-y", "@modelcontextprotocol/server-filesystem"])
            client = MCPClient(transport)
            
            await client.connect()
            tools = await client.list_tools()
            result = await client.call_tool("read_file", {"path": "/etc/hosts"})
            await client.disconnect()
            
        Using context manager (recommended)::
        
            async with MCPClient(transport) as client:
                tools = await client.list_tools()
                for tool in tools:
                    print(f"Available tool: {tool.name}")
                    
                result = await client.call_tool("tool_name", {"arg": "value"})
                
        With HTTP transport::
        
            from haive.mcp.client import HttpTransport
            
            transport = HttpTransport("http://localhost:8080/mcp")
            async with MCPClient(transport) as client:
                resources = await client.list_resources()
                content = await client.read_resource("file://config.json")
                
        With notification handling::
        
            def on_tool_list_changed(params):
                print("Tool list updated!")
                
            client.add_notification_handler("tools/list_changed", on_tool_list_changed)
            
        Error handling::
        
            try:
                async with MCPClient(transport) as client:
                    result = await client.call_tool("nonexistent", {})
            except MCPToolError as e:
                print(f"Tool error: {e}")
            except MCPConnectionError as e:
                print(f"Connection error: {e}")
    """
    
    def __init__(
        self,
        transport: MCPTransport,
        timeout: float = 30.0,
        client_info: Optional[Dict[str, Any]] = None,
        auto_reconnect: bool = False,
        max_reconnect_attempts: int = 3
    ):
        """Initialize MCP client.
        
        Args:
            transport: Transport implementation (STDIO, HTTP, etc.)
            timeout: Default timeout for operations
            client_info: Client information for server handshake
            auto_reconnect: Whether to automatically reconnect on failures
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.transport = transport
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # Initialize protocol layer
        self.protocol = MCPProtocol(
            transport=transport,
            timeout=timeout,
            client_info=client_info or {
                "name": "haive-mcp-client",
                "version": "1.0.0"
            }
        )
        
        # Connection state
        self._connected = False
        self._connecting = False
        self._reconnect_count = 0
        self._connection_lock = asyncio.Lock()
        
        # Cached server information
        self._server_info: Optional[Dict[str, Any]] = None
        self._capabilities: Optional[List[MCPCapability]] = None
        self._tools_cache: Optional[List[MCPTool]] = None
        self._resources_cache: Optional[List[MCPResource]] = None
        self._prompts_cache: Optional[List[MCPPrompt]] = None
        
        # Setup default notification handlers
        self._setup_default_handlers()
        
    async def connect(self) -> Dict[str, Any]:
        """Connect to the MCP server and perform initialization.
        
        This method establishes the connection and performs the MCP
        initialization handshake, including capability negotiation.
        
        Returns:
            Server information and capabilities
            
        Raises:
            MCPConnectionError: If connection fails
            MCPProtocolError: If protocol handshake fails
        """
        async with self._connection_lock:
            if self._connected:
                return self._server_info
                
            if self._connecting:
                # Another connection attempt in progress
                raise MCPConnectionError("Connection attempt already in progress")
                
            self._connecting = True
            
            try:
                logger.info("Connecting to MCP server")
                
                # Initialize protocol (this handles transport connection)
                init_result = await self.protocol.initialize()
                
                # Cache server information
                self._server_info = init_result
                self._capabilities = [
                    MCPCapability(cap) for cap in init_result.get("capabilities", [])
                ]
                
                self._connected = True
                self._connecting = False
                self._reconnect_count = 0
                
                logger.info(
                    f"Connected to MCP server: {init_result.get('serverInfo', {}).get('name', 'unknown')}"
                )
                
                return init_result
                
            except Exception as e:
                self._connecting = False
                logger.error(f"Failed to connect to MCP server: {e}")
                
                if isinstance(e, (MCPConnectionError, MCPProtocolError)):
                    raise
                raise MCPConnectionError(f"Connection failed: {e}")
                
    async def disconnect(self) -> None:
        """Disconnect from the MCP server gracefully.
        
        This method cleanly shuts down the MCP connection and cleans up
        all resources. It's safe to call multiple times.
        """
        async with self._connection_lock:
            if not self._connected:
                return
                
            try:
                logger.info("Disconnecting from MCP server")
                await self.protocol.shutdown()
                
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
                
            finally:
                self._connected = False
                self._connecting = False
                self._clear_cache()
                
    async def is_connected(self) -> bool:
        """Check if client is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
        
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information from initialization.
        
        Returns:
            Server information dictionary
            
        Raises:
            MCPConnectionError: If not connected
        """
        await self._ensure_connected()
        return self._server_info
        
    async def get_capabilities(self) -> List[MCPCapability]:
        """Get server capabilities.
        
        Returns:
            List of server capabilities
            
        Raises:
            MCPConnectionError: If not connected
        """
        await self._ensure_connected()
        return self._capabilities
        
    async def list_tools(self, use_cache: bool = True) -> List[MCPTool]:
        """List available tools from the server.
        
        Args:
            use_cache: Whether to use cached results if available
            
        Returns:
            List of available tools
            
        Raises:
            MCPCapabilityError: If tools capability not supported
            MCPProtocolError: If request fails
        """
        await self._ensure_connected()
        
        if use_cache and self._tools_cache is not None:
            return self._tools_cache
            
        try:
            tools = await self.protocol.list_tools()
            self._tools_cache = tools
            return tools
            
        except Exception as e:
            await self._handle_operation_error(e, "list_tools")
            raise
            
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Call a tool on the server.
        
        Args:
            name: Tool name to call
            arguments: Tool arguments
            timeout: Call timeout (uses default if None)
            
        Returns:
            Tool execution result
            
        Raises:
            MCPToolError: If tool execution fails
            MCPProtocolError: If request fails
        """
        await self._ensure_connected()
        
        try:
            # Use custom timeout if provided
            if timeout is not None:
                original_timeout = self.protocol.timeout
                self.protocol.timeout = timeout
                
            try:
                result = await self.protocol.call_tool(name, arguments)
                return result
            finally:
                if timeout is not None:
                    self.protocol.timeout = original_timeout
                    
        except Exception as e:
            await self._handle_operation_error(e, "call_tool", {"tool": name})
            raise
            
    async def list_prompts(self, use_cache: bool = True) -> List[MCPPrompt]:
        """List available prompts from the server.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            List of available prompts
            
        Raises:
            MCPCapabilityError: If prompts capability not supported
        """
        await self._ensure_connected()
        
        if use_cache and self._prompts_cache is not None:
            return self._prompts_cache
            
        try:
            prompts = await self.protocol.list_prompts()
            self._prompts_cache = prompts
            return prompts
            
        except Exception as e:
            await self._handle_operation_error(e, "list_prompts")
            raise
            
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get a prompt from the server.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            
        Returns:
            Prompt content and metadata
        """
        await self._ensure_connected()
        
        try:
            return await self.protocol.get_prompt(name, arguments)
            
        except Exception as e:
            await self._handle_operation_error(e, "get_prompt", {"prompt": name})
            raise
            
    async def list_resources(self, use_cache: bool = True) -> List[MCPResource]:
        """List available resources from the server.
        
        Args:
            use_cache: Whether to use cached results
            
        Returns:
            List of available resources
        """
        await self._ensure_connected()
        
        if use_cache and self._resources_cache is not None:
            return self._resources_cache
            
        try:
            resources = await self.protocol.list_resources()
            self._resources_cache = resources
            return resources
            
        except Exception as e:
            await self._handle_operation_error(e, "list_resources")
            raise
            
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content and metadata
        """
        await self._ensure_connected()
        
        try:
            return await self.protocol.read_resource(uri)
            
        except Exception as e:
            await self._handle_operation_error(e, "read_resource", {"uri": uri})
            raise
            
    def add_notification_handler(
        self,
        method: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Add a handler for server notifications.
        
        Args:
            method: Notification method name
            handler: Async handler function
        """
        self.protocol.add_notification_handler(method, handler)
        
    def remove_notification_handler(
        self,
        method: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Remove a notification handler.
        
        Args:
            method: Notification method name
            handler: Handler function to remove
        """
        self.protocol.remove_notification_handler(method, handler)
        
    async def refresh_cache(self) -> None:
        """Refresh all cached server information.
        
        This re-fetches tools, prompts, and resources from the server
        and updates the local cache.
        """
        await self._ensure_connected()
        
        self._clear_cache()
        
        # Pre-load cache if capabilities support it
        if MCPCapability.TOOLS in self._capabilities:
            await self.list_tools(use_cache=False)
            
        if MCPCapability.PROMPTS in self._capabilities:
            await self.list_prompts(use_cache=False)
            
        if MCPCapability.RESOURCES in self._capabilities:
            await self.list_resources(use_cache=False)
            
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the MCP connection.
        
        Returns:
            Health check results including connectivity and capabilities
        """
        health = {
            "connected": self._connected,
            "server_info": self._server_info,
            "capabilities": [cap.value for cap in (self._capabilities or [])],
            "transport_type": type(self.transport).__name__,
            "error": None
        }
        
        if not self._connected:
            health["error"] = "Not connected"
            return health
            
        try:
            # Try a simple operation to verify connectivity
            if MCPCapability.TOOLS in self._capabilities:
                await self.list_tools()
                health["tools_accessible"] = True
            else:
                health["tools_accessible"] = False
                
        except Exception as e:
            health["error"] = str(e)
            health["tools_accessible"] = False
            
        return health
        
    async def _ensure_connected(self) -> None:
        """Ensure client is connected, attempting reconnection if needed."""
        if self._connected:
            return
            
        if self.auto_reconnect and self._reconnect_count < self.max_reconnect_attempts:
            logger.info(f"Attempting reconnection (attempt {self._reconnect_count + 1})")
            self._reconnect_count += 1
            try:
                await self.connect()
                return
            except Exception as e:
                logger.warning(f"Reconnection attempt failed: {e}")
                
        raise MCPConnectionError("Not connected to MCP server")
        
    async def _handle_operation_error(
        self,
        error: Exception,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle errors during operations, potentially triggering reconnection."""
        logger.error(f"Error during {operation}: {error}")
        
        if isinstance(error, MCPConnectionError):
            self._connected = False
            
            if self.auto_reconnect:
                logger.info("Connection lost, will attempt reconnection on next operation")
                
    def _clear_cache(self) -> None:
        """Clear all cached server information."""
        self._tools_cache = None
        self._resources_cache = None
        self._prompts_cache = None
        
    def _setup_default_handlers(self) -> None:
        """Setup default notification handlers for cache invalidation."""
        async def on_tools_changed(params: Dict[str, Any]) -> None:
            """Handle tools list changed notification."""
            logger.info("Server tools list changed, clearing cache")
            self._tools_cache = None
            
        async def on_prompts_changed(params: Dict[str, Any]) -> None:
            """Handle prompts list changed notification."""
            logger.info("Server prompts list changed, clearing cache")
            self._prompts_cache = None
            
        async def on_resources_changed(params: Dict[str, Any]) -> None:
            """Handle resources list changed notification."""
            logger.info("Server resources list changed, clearing cache")
            self._resources_cache = None
            
        # Register default handlers
        self.add_notification_handler("tools/list_changed", on_tools_changed)
        self.add_notification_handler("prompts/list_changed", on_prompts_changed)
        self.add_notification_handler("resources/list_changed", on_resources_changed)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()