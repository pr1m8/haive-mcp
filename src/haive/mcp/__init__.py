"""Haive MCP Package - Model Context Protocol implementation for agent communication.

This package provides a comprehensive implementation of the Model Context Protocol (MCP),
which enables standardized communication between Haive agents, tools, and external systems.
The MCP implementation facilitates secure, reliable, and efficient message exchange in
distributed AI systems.

The MCP package includes:

Core Protocol Features:
    - Message serialization and deserialization
    - Protocol versioning and compatibility checking
    - Message routing and delivery guarantees
    - Error handling and recovery mechanisms
    - Authentication and authorization

Communication Patterns:
    - Request-response messaging
    - Publish-subscribe event handling
    - Streaming data transfer
    - Broadcast messaging
    - Point-to-point communication

Integration Capabilities:
    - WebSocket connections for real-time communication
    - HTTP/REST API endpoints
    - Message queue integration (Redis, RabbitMQ)
    - File-based message persistence
    - Memory-based message buffering

Security Features:
    - Message encryption and signing
    - Identity verification
    - Rate limiting and throttling
    - Access control and permissions
    - Audit logging and monitoring

Usage:
    ```python
    from haive.mcp import MCPClient, MCPServer, Message

    # Create an MCP server
    server = MCPServer(
        host="localhost",
        port=8080,
        auth_required=True
    )

    # Register message handlers
    @server.handle("agent.request")
    async def handle_agent_request(message: Message):
        # Process agent request
        return {"status": "success", "data": process_request(message.data)}

    # Start the server
    await server.start()

    # Create an MCP client
    client = MCPClient("ws://localhost:8080")
    await client.connect()

    # Send a message
    response = await client.send("agent.request", {"query": "Hello"})
    print(response.data)
    ```

Architecture:
    The MCP implementation follows a layered architecture:
    - Transport Layer: WebSocket, HTTP, TCP connections
    - Protocol Layer: Message framing, routing, delivery
    - Application Layer: Business logic and handlers
    - Security Layer: Authentication, encryption, authorization

The package is designed to be:
- Protocol-agnostic: Support multiple transport mechanisms
- Scalable: Handle high-throughput message processing
- Reliable: Ensure message delivery and ordering
- Secure: Protect against common attack vectors
- Extensible: Allow custom message types and handlers

For detailed information about specific components, see the individual
module documentation.
"""

__version__ = "0.1.0"

# Import core MCP components
try:
    from haive.mcp.client import MCPClient
    from haive.mcp.message import Message, MessageType
    from haive.mcp.protocol import MCPProtocol
    from haive.mcp.server import MCPServer

    MCP_AVAILABLE = True
except ImportError:
    # Graceful degradation if MCP components aren't fully implemented
    MCP_AVAILABLE = False

__all__ = [
    "__version__",
]

if MCP_AVAILABLE:
    __all__.extend(
        [
            "MCPClient",
            "MCPProtocol",
            "MCPServer",
            "Message",
            "MessageType",
        ]
    )
