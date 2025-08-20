"""MCP Protocol Implementation.

This module implements the Model Context Protocol (MCP) JSON-RPC based
communication protocol. It handles the protocol-level details including
message framing, request/response matching, and capability negotiation.

The protocol implementation is transport-agnostic and works with any
transport that implements the MCPTransport interface.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Union, Callable, Awaitable
from enum import Enum
from pydantic import BaseModel, Field

from .exceptions import (
    MCPProtocolError,
    MCPCapabilityError,
    MCPToolError,
    MCPTimeoutError
)

logger = logging.getLogger(__name__)


class MCPProtocolVersion(str, Enum):
    """Supported MCP protocol versions."""
    V1_0 = "1.0"
    V0_9 = "0.9"


class MCPCapability(str, Enum):
    """Standard MCP capabilities."""
    TOOLS = "tools"
    LOGGING = "logging"
    PROMPTS = "prompts"
    RESOURCES = "resources"
    SAMPLING = "sampling"


class MCPMessageType(str, Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


class MCPMethod(str, Enum):
    """Standard MCP methods."""
    # Initialization
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"
    
    # Tool operations
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Prompt operations
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Resource operations
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    
    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"
    
    # Notifications
    CANCELLED = "cancelled"
    PROGRESS = "progress"
    RESOURCE_UPDATED = "resources/updated"
    RESOURCE_LIST_CHANGED = "resources/list_changed"
    TOOL_LIST_CHANGED = "tools/list_changed"
    PROMPT_LIST_CHANGED = "prompts/list_changed"


class MCPMessage(BaseModel):
    """Base MCP message."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Optional[Union[str, int]] = Field(default=None, description="Message ID")
    method: Optional[str] = Field(default=None, description="Method name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Method parameters")
    result: Optional[Any] = Field(default=None, description="Response result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    inputSchema: Dict[str, Any] = Field(description="JSON schema for tool input")


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str = Field(description="Prompt name")
    description: str = Field(description="Prompt description")
    arguments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Prompt arguments")


class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str = Field(description="Resource URI")
    name: str = Field(description="Resource name")
    description: Optional[str] = Field(default=None, description="Resource description")
    mimeType: Optional[str] = Field(default=None, description="MIME type")


class MCPProtocol:
    """MCP protocol implementation.
    
    This class handles the MCP protocol layer, including:
        - Message serialization/deserialization
        - Request/response matching
        - Capability negotiation
        - Protocol state management
        - Error handling
        
    The protocol is transport-agnostic and works with any MCPTransport
    implementation. It provides a clean async API for MCP operations.
    
    Examples:
        Basic protocol usage::
        
            from haive.mcp.client.transport import StdioTransport
            from haive.mcp.client.protocol import MCPProtocol
            
            transport = StdioTransport("npx", ["-y", "@modelcontextprotocol/server-filesystem"])
            protocol = MCPProtocol(transport)
            
            await protocol.initialize()
            tools = await protocol.list_tools()
            result = await protocol.call_tool("read_file", {"path": "/etc/hosts"})
            await protocol.shutdown()
            
        With context manager::
        
            async with MCPProtocol(transport) as protocol:
                tools = await protocol.list_tools()
                result = await protocol.call_tool("tool_name", args)
    """
    
    def __init__(
        self,
        transport,
        timeout: float = 30.0,
        client_info: Optional[Dict[str, Any]] = None
    ):
        """Initialize MCP protocol.
        
        Args:
            transport: Transport implementation
            timeout: Default timeout for requests
            client_info: Client information for initialization
        """
        self.transport = transport
        self.timeout = timeout
        self.client_info = client_info or {
            "name": "haive-mcp-client",
            "version": "1.0.0"
        }
        
        # Protocol state
        self.initialized = False
        self.server_info: Optional[Dict[str, Any]] = None
        self.server_capabilities: Set[MCPCapability] = set()
        self.protocol_version: Optional[MCPProtocolVersion] = None
        
        # Request tracking
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_counter = 0
        self._message_handler_task: Optional[asyncio.Task] = None
        
        # Notification handlers
        self._notification_handlers: Dict[str, List[Callable]] = {}
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize the MCP connection.
        
        This performs the MCP initialization handshake, including capability
        negotiation and protocol version agreement.
        
        Returns:
            Server information and capabilities
            
        Raises:
            MCPProtocolError: If initialization fails
            MCPCapabilityError: If capabilities are incompatible
        """
        if self.initialized:
            return self.server_info
            
        try:
            # Connect transport
            await self.transport.connect()
            
            # Start message handler
            self._message_handler_task = asyncio.create_task(self._handle_messages())
            
            # Send initialize request
            init_params = {
                "protocolVersion": MCPProtocolVersion.V1_0.value,
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "clientInfo": self.client_info
            }
            
            logger.info("Sending MCP initialize request")
            response = await self._send_request(MCPMethod.INITIALIZE.value, init_params)
            
            # Process initialize response
            if "error" in response:
                raise MCPProtocolError(
                    f"Initialization failed: {response['error']}",
                    error_code=response['error'].get('code'),
                    details=response['error']
                )
                
            result = response.get("result", {})
            
            # Handle protocol version - some servers return non-standard versions
            protocol_version_raw = result.get("protocolVersion", "1.0")
            try:
                self.protocol_version = MCPProtocolVersion(protocol_version_raw)
            except ValueError:
                # If server returns non-standard version, default to 1.0
                logger.warning(f"Server returned non-standard protocol version '{protocol_version_raw}', using '1.0'")
                self.protocol_version = MCPProtocolVersion.V1_0
                
            self.server_info = result.get("serverInfo", {})
            
            # Extract server capabilities
            server_caps = result.get("capabilities", {})
            self.server_capabilities.clear()
            
            if "tools" in server_caps:
                self.server_capabilities.add(MCPCapability.TOOLS)
            if "logging" in server_caps:
                self.server_capabilities.add(MCPCapability.LOGGING)
            if "prompts" in server_caps:
                self.server_capabilities.add(MCPCapability.PROMPTS)
            if "resources" in server_caps:
                self.server_capabilities.add(MCPCapability.RESOURCES)
                
            # Send initialized notification
            await self._send_notification(MCPMethod.INITIALIZED.value, {})
            
            self.initialized = True
            logger.info(f"MCP initialized with server: {self.server_info.get('name', 'unknown')}")
            logger.info(f"Server capabilities: {list(self.server_capabilities)}")
            
            return {
                "serverInfo": self.server_info,
                "capabilities": list(self.server_capabilities),
                "protocolVersion": self.protocol_version.value
            }
            
        except Exception as e:
            await self._cleanup()
            if isinstance(e, (MCPProtocolError, MCPCapabilityError)):
                raise
            raise MCPProtocolError(f"Initialization failed: {e}")
            
    async def shutdown(self) -> None:
        """Shutdown the MCP connection gracefully."""
        if not self.initialized:
            return
            
        await self._cleanup()
        self.initialized = False
        logger.info("MCP connection shutdown")
        
    async def _cleanup(self) -> None:
        """Clean up protocol resources."""
        # Cancel message handler
        if self._message_handler_task and not self._message_handler_task.done():
            self._message_handler_task.cancel()
            try:
                await self._message_handler_task
            except asyncio.CancelledError:
                pass
            self._message_handler_task = None
            
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        # Disconnect transport
        await self.transport.disconnect()
        
    async def list_tools(self) -> List[MCPTool]:
        """List available tools from the server.
        
        Returns:
            List of available tools
            
        Raises:
            MCPCapabilityError: If tools capability not supported
            MCPProtocolError: If request fails
        """
        self._check_capability(MCPCapability.TOOLS)
        
        response = await self._send_request(MCPMethod.TOOLS_LIST.value, {})
        
        if "error" in response:
            raise MCPProtocolError(
                f"Failed to list tools: {response['error']}",
                error_code=response['error'].get('code')
            )
            
        tools_data = response.get("result", {}).get("tools", [])
        return [MCPTool(**tool) for tool in tools_data]
        
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a tool on the server.
        
        Args:
            name: Tool name to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
            
        Raises:
            MCPCapabilityError: If tools capability not supported
            MCPToolError: If tool execution fails
            MCPProtocolError: If request fails
        """
        self._check_capability(MCPCapability.TOOLS)
        
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        
        response = await self._send_request(MCPMethod.TOOLS_CALL.value, params)
        
        if "error" in response:
            error = response["error"]
            raise MCPToolError(
                f"Tool call failed: {error.get('message', 'Unknown error')}",
                error_code=error.get('code'),
                details={"tool": name, "arguments": arguments, "error": error}
            )
            
        return response.get("result")
        
    async def list_prompts(self) -> List[MCPPrompt]:
        """List available prompts from the server.
        
        Returns:
            List of available prompts
            
        Raises:
            MCPCapabilityError: If prompts capability not supported
        """
        self._check_capability(MCPCapability.PROMPTS)
        
        response = await self._send_request(MCPMethod.PROMPTS_LIST.value, {})
        
        if "error" in response:
            raise MCPProtocolError(
                f"Failed to list prompts: {response['error']}",
                error_code=response['error'].get('code')
            )
            
        prompts_data = response.get("result", {}).get("prompts", [])
        return [MCPPrompt(**prompt) for prompt in prompts_data]
        
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
        self._check_capability(MCPCapability.PROMPTS)
        
        params = {
            "name": name,
            "arguments": arguments or {}
        }
        
        response = await self._send_request(MCPMethod.PROMPTS_GET.value, params)
        
        if "error" in response:
            raise MCPProtocolError(
                f"Failed to get prompt: {response['error']}",
                error_code=response['error'].get('code')
            )
            
        return response.get("result", {})
        
    async def list_resources(self) -> List[MCPResource]:
        """List available resources from the server.
        
        Returns:
            List of available resources
        """
        self._check_capability(MCPCapability.RESOURCES)
        
        response = await self._send_request(MCPMethod.RESOURCES_LIST.value, {})
        
        if "error" in response:
            raise MCPProtocolError(
                f"Failed to list resources: {response['error']}",
                error_code=response['error'].get('code')
            )
            
        resources_data = response.get("result", {}).get("resources", [])
        return [MCPResource(**resource) for resource in resources_data]
        
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server.
        
        Args:
            uri: Resource URI to read
            
        Returns:
            Resource content and metadata
        """
        self._check_capability(MCPCapability.RESOURCES)
        
        params = {"uri": uri}
        response = await self._send_request(MCPMethod.RESOURCES_READ.value, params)
        
        if "error" in response:
            raise MCPProtocolError(
                f"Failed to read resource: {response['error']}",
                error_code=response['error'].get('code')
            )
            
        return response.get("result", {})
        
    def add_notification_handler(
        self,
        method: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Add a handler for notifications.
        
        Args:
            method: Notification method name
            handler: Async handler function
        """
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)
        
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
        if method in self._notification_handlers:
            try:
                self._notification_handlers[method].remove(handler)
            except ValueError:
                pass
                
    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send a request and wait for response.
        
        Args:
            method: Method name
            params: Request parameters
            timeout: Request timeout (uses default if None)
            
        Returns:
            Response message
        """
        if not self.initialized and method != MCPMethod.INITIALIZE.value:
            raise MCPProtocolError("Protocol not initialized")
            
        # Generate request ID
        self._request_counter += 1
        request_id = str(self._request_counter)
        
        # Create request message
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        response_future = asyncio.Future()
        self._pending_requests[request_id] = response_future
        
        try:
            # Send request
            await self.transport.send_message(message)
            
            # Wait for response
            use_timeout = timeout or self.timeout
            response = await asyncio.wait_for(response_future, timeout=use_timeout)
            
            return response
            
        except asyncio.TimeoutError:
            # Clean up on timeout
            self._pending_requests.pop(request_id, None)
            raise MCPTimeoutError(f"Request {method} timed out after {use_timeout}s")
        except Exception:
            # Clean up on error
            self._pending_requests.pop(request_id, None)
            raise
            
    async def _send_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send a notification (no response expected).
        
        Args:
            method: Method name
            params: Notification parameters
        """
        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        
        await self.transport.send_message(message)
        
    async def _handle_messages(self) -> None:
        """Background task to handle incoming messages."""
        try:
            while True:
                message = await self.transport.receive_message()
                await self._process_message(message)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Message handler error: {e}")
            
    async def _process_message(self, message: Dict[str, Any]) -> None:
        """Process an incoming message.
        
        Args:
            message: Received message
        """
        try:
            msg = MCPMessage(**message)
            
            # Handle response
            if msg.id and str(msg.id) in self._pending_requests:
                future = self._pending_requests.pop(str(msg.id))
                if not future.done():
                    future.set_result(message)
                return
                
            # Handle notification
            if msg.method and msg.id is None:
                await self._handle_notification(msg.method, msg.params or {})
                return
                
            logger.warning(f"Unhandled message: {message}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    async def _handle_notification(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> None:
        """Handle a notification message.
        
        Args:
            method: Notification method
            params: Notification parameters
        """
        logger.debug(f"Received notification: {method}")
        
        # Call registered handlers
        handlers = self._notification_handlers.get(method, [])
        for handler in handlers:
            try:
                await handler(params)
            except Exception as e:
                logger.error(f"Notification handler error: {e}")
                
    def _check_capability(self, capability: MCPCapability) -> None:
        """Check if server supports a capability.
        
        Args:
            capability: Required capability
            
        Raises:
            MCPCapabilityError: If capability not supported
        """
        if capability not in self.server_capabilities:
            raise MCPCapabilityError(
                f"Server doesn't support {capability.value} capability",
                details={
                    "required": capability.value,
                    "supported": list(self.server_capabilities)
                }
            )
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()