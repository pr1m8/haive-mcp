#!/usr/bin/env python3
"""Debug transport issues."""

from haive.mcp.config import MCPServerConfig, MCPTransport

# Test transport
config = MCPServerConfig(
    name="test",
    transport=MCPTransport.STDIO,
    command="echo",
    args=["test"]
)

print(f"Transport: {config.transport}")
print(f"Transport type: {type(config.transport)}")
print(f"Transport value: {config.transport.value}")
print(f"Is 'stdio': {config.transport.value == 'stdio'}")

# Test connection creation
try:
    from langchain_mcp_adapters.client import StdioConnection
    print("StdioConnection import successful")
    
    # Try to create connection
    connection = StdioConnection(
        command=config.command,
        args=config.args or [],
        env=config.env or {}
    )
    print(f"Connection created: {connection}")
    
except Exception as e:
    print(f"Error creating connection: {e}")
    import traceback
    traceback.print_exc()