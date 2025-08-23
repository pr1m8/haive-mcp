"""MCP Client Implementation Package.

This package provides native MCP protocol client implementation for connecting
to and communicating with MCP servers according to the Model Context Protocol
specification.

Key Components
--------------

**Core Classes**
    - :class:`MCPClient`: Main client for protocol communication
    - :class:`MCPTransport`: Transport layer abstraction  
    - :class:`MCPConnection`: Connection management
    - :class:`MCPProtocol`: Protocol implementation

**Transport Support**
    - **STDIO**: Communication via stdin/stdout
    - **HTTP**: RESTful communication  
    - **SSE**: Server-sent events
    - **WebSocket**: Real-time bidirectional communication

Usage Examples
--------------

Basic Connection
~~~~~~~~~~~~~~~~

.. code-block:: python

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

Context Manager Usage
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    async with MCPClient(transport) as client:
        tools = await client.list_tools()
        result = await client.call_tool("tool_name", args)

Available Classes
-----------------

Transport Classes
~~~~~~~~~~~~~~~~~
- :class:`StdioTransport` - Standard I/O transport
- :class:`HttpTransport` - HTTP-based transport
- :class:`SseTransport` - Server-Sent Events transport
- :class:`WebSocketTransport` - WebSocket transport

Exception Classes
~~~~~~~~~~~~~~~~~
- :class:`MCPError` - Base MCP exception
- :class:`MCPConnectionError` - Connection-related errors
- :class:`MCPProtocolError` - Protocol violation errors
- :class:`MCPTimeoutError` - Timeout-related errors
- :class:`MCPTransportError` - Transport layer errors
- :class:`MCPAuthenticationError` - Authentication failures
- :class:`MCPCapabilityError` - Capability negotiation errors
- :class:`MCPToolError` - Tool execution errors

.. note::
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