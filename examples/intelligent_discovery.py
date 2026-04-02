#!/usr/bin/env python3
"""Intelligent MCP Discovery - Auto-discover servers based on task needs.

Demonstrates the IntelligentMCPAgent which analyzes user requests and
automatically discovers and installs appropriate MCP servers from the
database of 1,960+ servers.

Usage:
    poetry run python examples/intelligent_discovery.py
"""

import asyncio

from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.agents.intelligent_mcp_agent import IntelligentMCPAgent


async def main():
    # Create an intelligent agent with auto-discovery
    agent = IntelligentMCPAgent(
        engine=AugLLMConfig(),
        auto_discover=True,
        require_approval=True,  # Ask before installing servers
    )

    await agent.setup()

    # The agent analyzes what you need and finds appropriate MCP servers
    result = await agent.arun(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Find MCP servers that can help me work with GitHub repositories",
                }
            ]
        }
    )

    print("Discovery result:", result)


if __name__ == "__main__":
    asyncio.run(main())
