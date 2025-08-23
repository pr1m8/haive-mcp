"""MCP Server Management Package.

This package provides comprehensive server management infrastructure for Model Context 
Protocol (MCP) servers with full Pydantic validation, type safety, and runtime monitoring.
The package has been refactored to use a modern Pydantic-based architecture while maintaining
complete backward compatibility with existing code.

Key Components
--------------

**Server Management**
    - :class:`MCPServerManager` - Pydantic-enhanced server manager with validation and type safety
    - :class:`MCPServerConfig` - Configuration management with Pydantic models
    - :class:`MCPServerModels` - Data models for server state and operations
    - :class:`MCPCompatibilityManager` - Backward compatibility layer

**Server Types**
    - **HTTP Server**: RESTful MCP server implementation
    - **Dataflow Server**: Integration with haive-dataflow processing
    - **Simple Server**: Lightweight server for basic operations
    - **Non-Interactive Server**: Batch processing server

Usage Examples
--------------

Basic Server Management
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp.servers import MCPServerManager, MCPServerConfig

    # Create server configuration
    config = MCPServerConfig(
        name="filesystem_server",
        transport="stdio", 
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem"]
    )

    # Initialize server manager
    manager = MCPServerManager()
    await manager.start_server(config)

    # Monitor server health
    status = await manager.get_server_status("filesystem_server")
    print(f"Server status: {status}")

HTTP Server Setup
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from haive.mcp.servers import HTTPMCPServer

    # Create HTTP-based MCP server
    server = HTTPMCPServer(
        host="localhost",
        port=8080,
        tools=["file_operations", "web_search"]
    )

    # Start server
    await server.start()

Available Classes
-----------------

Manager Classes
~~~~~~~~~~~~~~~
- :class:`MCPServerManager` - Primary server lifecycle management
- :class:`MCPServerManagerV2` - Enhanced version with additional features
- :class:`MCPServerManagerRefactored` - Latest refactored implementation

Configuration
~~~~~~~~~~~~~
- :class:`MCPServerConfig` - Server configuration model
- :class:`MCPServerModels` - Data models for server operations
- :class:`MCPCompatibilityManager` - Compatibility management

Server Implementations
~~~~~~~~~~~~~~~~~~~~~~
- :class:`HTTPMCPServer` - HTTP-based server
- :class:`DataflowMCPServer` - Dataflow integration server
- :class:`SimpleMCPServer` - Lightweight server
- :class:`NonInteractiveMCPServer` - Batch processing server

.. note::
   This package uses modern Pydantic-based architecture for type safety
   and validation while maintaining full backward compatibility with
   existing server implementations.
"""

from haive.mcp.servers.dataflow_mcp_server import AgentCreationRequest
from haive.mcp.servers.http_server import run_server
from haive.mcp.servers.simple_http_server import create_app

# Import the refactored manager and models
from haive.mcp.servers.mcp_server_manager import MCPServerManager
from haive.mcp.servers.models import MCPServerConfig, MCPServerInfo, MCPTransport

SSEServerTransport = None  # TODO: Implement SSE transport

__all__ = [
    # Core exports
    "AgentCreationRequest",
    "SSEServerTransport", 
    "create_app",
    "run_server",
    "MCPServerManager",
    
    # Pydantic models
    "MCPServerConfig",
    "MCPServerInfo", 
    "MCPTransport",
]
