#!/usr/bin/env python3
"""Debug actual connection process."""

import asyncio
from haive.mcp.config import MCPServerConfig, MCPTransport

async def test_connection():
    # Test transport
    config = MCPServerConfig(
        name="test",
        transport=MCPTransport.STDIO,
        command="echo",
        args=["test"],
        env={}
    )

    print(f"Testing connection with: {config.command} {config.args}")
    
    try:
        from langchain_mcp_adapters.client import StdioConnection, create_session
        print("Imports successful")
        
        # Create connection
        connection = StdioConnection(
            transport="stdio",
            command=config.command,
            args=config.args or [],
            env=config.env or {},
            cwd=None,
            encoding="utf-8",
            encoding_error_handler="strict",
            session_kwargs=None
        )
        print(f"Connection created: {connection}")
        
        # Try to create session
        print("Attempting to create session...")
        async with create_session(connection) as session:
            print(f"Session created successfully: {session}")
            
            # Try to list tools
            from langchain_mcp_adapters.client import load_mcp_tools
            tools = await load_mcp_tools(session)
            print(f"Tools loaded: {len(tools) if tools else 0}")
        
        print("Connection test successful!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())