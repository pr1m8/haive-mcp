#!/usr/bin/env python3
"""Basic MCP Agent - Static server configuration.

Demonstrates connecting to MCP servers with a known configuration.
This is the simplest way to use haive-mcp: define your servers upfront
and let the agent use their tools.

Usage:
    poetry run python examples/basic_mcp_agent.py
"""

import asyncio

from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.agents.mcp_agent import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport


async def main():
    # Configure MCP servers explicitly
    config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport=MCPTransport.STDIO,
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                description="Local filesystem operations",
                capabilities=["file_read", "file_write", "directory_list"],
            ),
        },
    )

    # Create the agent with MCP config
    agent = MCPAgent(
        engine=AugLLMConfig(),
        mcp_config=config,
    )

    # Initialize MCP connections
    await agent.setup()

    # Run a task - the agent can now use filesystem tools
    result = await agent.arun(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "List the files in the /tmp directory",
                }
            ]
        }
    )

    print("Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
