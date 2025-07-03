"""MCP Server implementations and utilities.

This module contains implementations of MCP servers using FastMCP and utilities
for creating custom MCP servers. It provides base classes, decorators, and
helper functions for building MCP servers that can be used with the Haive framework.

The servers module includes:
- Base server classes for common patterns
- Utility decorators for tool and resource creation
- Example server implementations
- Server lifecycle management utilities

Classes:
    BaseHaiveMCPServer: Base class for Haive MCP servers
    FileSystemServer: MCP server for file system operations
    DatabaseServer: MCP server for database operations
    APIServer: MCP server for API integrations

Example:
    Creating a custom MCP server::

        from mcp.server import FastMCP
        from haive.mcp.servers import BaseHaiveMCPServer

        class MyCustomServer(BaseHaiveMCPServer):
            def __init__(self, name: str = "my-custom-server"):
                self.server = FastMCP(name)
                self.setup_tools()
                self.setup_resources()
            
            def setup_tools(self):
                @self.server.tool()
                async def process_data(data: str) -> str:
                    '''Process input data.'''
                    return f"Processed: {data}"
            
            def setup_resources(self):
                @self.server.resource("data://current")
                async def get_current_data() -> str:
                    '''Get current data state.'''
                    return "Current data state"

        # Run the server
        server = MyCustomServer()
        await server.run()

Advanced Usage:
    Building a server with state management::

        from mcp.server import FastMCP
        from haive.mcp.servers import BaseHaiveMCPServer
        
        class StatefulServer(BaseHaiveMCPServer):
            def __init__(self):
                super().__init__("stateful-server")
                self.state = {}
                
            def setup_tools(self):
                @self.server.tool()
                async def store_value(key: str, value: str) -> str:
                    '''Store a value in server state.'''
                    self.state[key] = value
                    return f"Stored {key}={value}"
                
                @self.server.tool()
                async def get_value(key: str) -> str:
                    '''Get a value from server state.'''
                    return self.state.get(key, "Key not found")

Server Categories:
    - **filesystem**: File and directory operations
    - **database**: Database connections and queries
    - **api**: External API integrations
    - **compute**: Computational operations
    - **utility**: General utility functions

See Also:
    mcp.server.FastMCP: Core FastMCP server implementation
    haive.mcp.config: Configuration for MCP servers
    haive.mcp.manager: Managing MCP server connections
"""

# Import server implementations as they are created
# This module serves as a namespace for server implementations

__all__ = [
    # Server classes will be exported here
    # "BaseHaiveMCPServer",
    # "FileSystemServer",
    # "DatabaseServer",
    # "APIServer",
]