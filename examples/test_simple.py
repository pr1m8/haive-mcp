"""Simple test to check MCP functionality without discovery module."""

import asyncio
import logging

from haive.core.engine.aug_llm import AugLLMConfig
from haive.core.models.llm.base import OpenAILLMConfig
from haive.mcp.agents import MCPAgent
from haive.mcp.config import MCPConfig, MCPServerConfig


logging.basicConfig(level=logging.INFO)


async def test_basic_mcp():
    """Test basic MCP functionality."""
    # Create engine using AugLLMConfig
    engine = AugLLMConfig(
        llm_config=OpenAILLMConfig(model="gpt-4o-mini", temperature=0.1),
        name="test_engine",
    )

    # Create MCP config without using discovery
    mcp_config = MCPConfig(
        enabled=True,
        servers={
            "filesystem": MCPServerConfig(
                name="filesystem",
                transport="stdio",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem"],
                capabilities=["file_read", "file_write", "directory_list"],
                description="Local filesystem operations",
            )
        },
    )

    # Create agent
    agent = MCPAgent(engine=engine, mcp_config=mcp_config, name="test_agent")

    # Setup
    try:
        await agent.setup()
        print("Agent setup successful!")

        # Check status
        status = agent.get_mcp_status()
        print(f"MCP Status: {status}")

        # Try to list files
        result = await agent.arun(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "List the Python files in the current directory",
                    }
                ]
            }
        )

        print(f"Agent response: {result}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_basic_mcp())
