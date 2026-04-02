#!/usr/bin/env python3
"""LangChain MCP Adapters - Bridge MCP tools into LangChain/LangGraph.

Demonstrates using langchain-mcp-adapters to convert MCP server tools
into LangChain-compatible tools that work with any LangChain agent.

This is useful when you want to use MCP tools directly with LangChain
or LangGraph without the full haive-mcp agent framework.

Usage:
    poetry run python examples/langchain_mcp_adapters.py

References:
    - langchain-mcp-adapters: https://github.com/langchain-ai/langchain-mcp-adapters
"""

import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI


async def main():
    # Define MCP servers to connect to
    server_configs = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "transport": "stdio",
        },
        # Example with uvx (Python-based MCP servers)
        # "fetch": {
        #     "command": "uvx",
        #     "args": ["mcp-server-fetch"],
        #     "transport": "stdio",
        # },
    }

    # Use the multi-server client to connect and get tools
    async with MultiServerMCPClient(server_configs) as client:
        # Get LangChain-compatible tools from all servers
        tools = client.get_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Create a LangGraph ReAct agent with the MCP tools
        model = ChatOpenAI(model="gpt-4o-mini")
        agent = create_react_agent(model, tools)

        # Run the agent
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "List files in /tmp"}]}
        )
        print("Result:", result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
