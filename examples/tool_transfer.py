#!/usr/bin/env python3
"""Tool Transfer - Share MCP tools between agents.

Demonstrates the TransferableMCPAgent which can export its MCP tools
to other agents, enabling collaborative multi-agent workflows.

Usage:
    poetry run python examples/tool_transfer.py
"""

import asyncio

from haive.core.engine.aug_llm import AugLLMConfig
from haive.mcp.agents.transferable_mcp_agent import TransferableMCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig, MCPTransport


async def main():
    # Create two agents with different MCP servers
    config_a = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport=MCPTransport.STDIO,
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            ),
        },
    )

    agent_a = TransferableMCPAgent(engine=AugLLMConfig(), mcp_config=config_a)
    agent_b = TransferableMCPAgent(engine=AugLLMConfig())

    await agent_a.setup()
    await agent_b.setup()

    # Transfer filesystem tools from agent A to agent B
    await agent_a.transfer_tools_to_agent(
        agent_b,
        tool_names=["file_read", "file_write"],
    )

    print("Tools transferred successfully!")
    print(f"Agent B now has tools: {[t.name for t in agent_b.tools]}")


if __name__ == "__main__":
    asyncio.run(main())
