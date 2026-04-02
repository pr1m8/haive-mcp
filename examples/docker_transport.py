#!/usr/bin/env python3
"""Docker Transport - Run MCP servers in Docker containers.

Demonstrates configuring MCP servers to run inside Docker containers,
providing isolation and reproducible environments for server execution.

Usage:
    poetry run python examples/docker_transport.py

Requirements:
    - Docker must be installed and running
    - The MCP server image must be available (pulled or built locally)
"""

import asyncio

from haive.mcp.config import MCPServerConfig, MCPTransport
from haive.mcp.manager import MCPManager


async def main():
    manager = MCPManager()

    # Configure an MCP server to run in a Docker container
    result = await manager.add_server(
        "postgres",
        MCPServerConfig(
            name="postgres",
            transport=MCPTransport.DOCKER,
            # Docker image to use
            command="mcp/postgres",
            # Environment variables passed to the container
            env={
                "POSTGRES_HOST": "host.docker.internal",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "mydb",
            },
            # Docker-specific options in args
            args=[
                "--network", "host",
            ],
            description="PostgreSQL MCP server in Docker",
            capabilities=["database_query", "schema_inspect"],
        ),
    )
    print(f"Docker server added: {result}")

    # Use the server just like any other transport
    tools = await manager.get_all_tools(refresh=True)
    print(f"Available tools: {[t.name for t in tools]}")


if __name__ == "__main__":
    asyncio.run(main())
