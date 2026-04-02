#!/usr/bin/env python3
"""LangChain MCP Adapters - Bridge MCP tools into LangChain/LangGraph.

Demonstrates using langchain-mcp-adapters to convert MCP server tools
into LangChain-compatible tools that work with any LangChain agent.

Usage:
    poetry run python examples/langchain_mcp_adapters.py

References:
    - langchain-mcp-adapters: https://github.com/langchain-ai/langchain-mcp-adapters
"""

import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    # Define MCP servers to connect to
    server_configs = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "transport": "stdio",
        },
        # Python-based MCP servers use uvx:
        # "fetch": {
        #     "command": "uvx",
        #     "args": ["mcp-server-fetch"],
        #     "transport": "stdio",
        # },
    }

    # Create client and get LangChain-compatible tools
    client = MultiServerMCPClient(server_configs)
    tools = await client.get_tools()

    print(f"Discovered {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {(tool.description or '')[:60]}")

    # These tools work directly with LangGraph create_react_agent:
    #
    #   from langgraph.prebuilt import create_react_agent
    #   from langchain_openai import ChatOpenAI
    #
    #   model = ChatOpenAI(model="gpt-4o-mini")
    #   agent = create_react_agent(model, tools)
    #   result = await agent.ainvoke(
    #       {"messages": [{"role": "user", "content": "List files in /tmp"}]}
    #   )

    # You can also generate these configs from the haive-mcp search:
    #
    #   from haive.mcp.self_query import MCPSelfQuery
    #   sq = MCPSelfQuery()
    #   config = sq.loader.generate_server_config("filesystem")
    #   # config = {"command": "npx", "args": [...], "transport": "stdio"}


if __name__ == "__main__":
    asyncio.run(main())
