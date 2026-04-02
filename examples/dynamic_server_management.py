#!/usr/bin/env python3
"""Dynamic Server Management - Add and manage MCP servers at runtime.

Demonstrates using MCPManager to dynamically add, monitor, and hot-reload
MCP servers without restarting your application.

Usage:
    poetry run python examples/dynamic_server_management.py
"""

import asyncio

from haive.mcp.config import MCPServerConfig, MCPTransport
from haive.mcp.manager import MCPManager


async def main():
    manager = MCPManager()

    # Add a server dynamically
    result = await manager.add_server(
        "filesystem",
        MCPServerConfig(
            name="filesystem",
            transport=MCPTransport.STDIO,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        ),
    )
    print(f"Server added: {result}")

    # Get all available tools from connected servers
    tools = await manager.get_all_tools(refresh=True)
    print(f"Available tools: {[t.name for t in tools]}")

    # Check server health
    status = manager.get_all_server_status()
    print(f"Server status: {status}")

    # Hot-reload a server (picks up config changes without restart)
    await manager.reload_server("filesystem")
    print("Server reloaded!")

    # Clean up
    await manager.remove_server("filesystem")
    print("Server removed.")


if __name__ == "__main__":
    asyncio.run(main())
