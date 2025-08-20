"""MCP Client Implementation Package.

This package provides native MCP protocol client implementation for connecting
to and communicating with MCP servers according to the Model Context Protocol
specification.

Key Classes:
    MCPClient: Main client for protocol communication
    MCPTransport: Transport layer abstraction
    MCPConnection: Connection management
    MCPProtocol: Protocol implementation

Transport Support:
    - STDIO: Communication via stdin/stdout
    - HTTP: RESTful communication
    - SSE: Server-sent events
    - WebSocket: Real-time bidirectional communication

Usage:
    Basic connection::

        from haive.mcp.client import MCPClient, StdioTransport

        # Create transport and client
        transport = StdioTransport(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"]
        )
        client = MCPClient(transport)

        # Connect and use
        await client.connect()
        tools = await client.list_tools()
        result = await client.call_tool("read_file", {"path": "/etc/hosts"})
        await client.disconnect()

    With context manager::

        async with MCPClient(transport) as client:
            tools = await client.list_tools()
            result = await client.call_tool("tool_name", args)

Note:
    This is a native implementation of the MCP protocol, designed to work
    with any MCP-compliant server. It handles the full protocol lifecycle
    including initialization, capability discovery, and tool execution.
"""

from .mcp_client import MCPClient
from .transport import (
    MCPTransport,
    StdioTransport,
    HttpTransport,
    SseTransport,
    WebSocketTransport,
)
from .connection import MCPConnection
from .protocol import MCPProtocol
from .exceptions import (
    MCPError,
    MCPConnectionError,
    MCPProtocolError,
    MCPTimeoutError,
    MCPTransportError,
    MCPAuthenticationError,
    MCPCapabilityError,
    MCPToolError,
)

__all__ = [
    "MCPClient",
    "MCPTransport",
    "StdioTransport", 
    "HttpTransport",
    "SseTransport",
    "WebSocketTransport",
    "MCPConnection",
    "MCPProtocol",
    "MCPError",
    "MCPConnectionError",
    "MCPProtocolError", 
    "MCPTimeoutError",
    "MCPTransportError",
    "MCPAuthenticationError",
    "MCPCapabilityError",
    "MCPToolError",
]