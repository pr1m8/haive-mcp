#!/usr/bin/env python3
"""Practical MCP + Haive Agent Integration Example.

This example demonstrates:
1. Searching for MCP tools by query
2. Creating a haive agent with discovered tool capabilities
3. Using the agent to perform tasks
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from haive.agents.react import ReactAgent

# Haive imports
from haive.agents.simple import SimpleAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import Tool


class MCPToolDemo:
    """Demonstrates MCP tool integration with haive agents."""

    def __init__(self):
        # Correct path to MCP data
        self.data_path = (
            Path(__file__).parent.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json"
        )
        self.servers_data = self.load_mcp_data()

    def load_mcp_data(self) -> list[dict[str, Any]]:
        """Load MCP servers data."""
        if not self.data_path.exists():
            return []

        with open(self.data_path) as f:
            data = json.load(f)
            return data.get("all_servers", [])

    def search_tools(self, query: str) -> list[dict[str, Any]]:
        """Simple search for MCP tools."""
        query_lower = query.lower()
        results = []

        for server in self.servers_data:
            name = server.get("name", "").lower()
            desc = server.get("description", "").lower()
            category = server.get("category", "").lower()
            tools = [t.lower() for t in server.get("tools", [])]

            # Simple matching
            if (
                query_lower in name
                or query_lower in desc
                or query_lower in category
                or any(query_lower in tool for tool in tools)
            ):
                results.append(server)

        # Sort by stars
        results.sort(key=lambda x: x.get("stars", 0) or 0, reverse=True)

        return results[:5]  # Top 5 results

    def create_mcp_tool_wrapper(self, server_info: dict[str, Any]) -> Tool:
        """Create a tool wrapper for an MCP server."""
        server_name = server_info.get("name", "unknown")
        description = server_info.get("description", "MCP tool")

        # This is a mock implementation - in reality, you would:
        # 1. Connect to the actual MCP server
        # 2. Use the MCP protocol to communicate
        # 3. Return real results

        def tool_function(input: str) -> str:
            """Mock MCP tool function."""
            return f"[MCP Tool '{server_name}'] Processed: {input}"

        return Tool(
            name=server_name.replace("-", "_").replace(" ", "_"),
            description=description[:100],  # Limit description length
            func=tool_function,
        )


async def demo_calculator_agent():
    """Demo: Create an agent with calculator capabilities."""
    demo = MCPToolDemo()

    # Search for calculator tools
    results = demo.search_tools("calculator")

    if results:
        for _i, _server in enumerate(results[:3], 1):
            pass

        # Use the first result
        selected = results[0]

        # Create tool wrapper
        calc_tool = demo.create_mcp_tool_wrapper(selected)

        # Create agent with the tool
        agent = SimpleAgent(
            name="calculator_agent",
            engine=AugLLMConfig(
                temperature=0.7,
                system_message="You are a helpful assistant with access to a calculator tool.",
            ),
            tools=[calc_tool],
        )

        # Test the agent
        await agent.arun("Calculate 42 * 17")
    else:
        pass


async def demo_database_agent():
    """Demo: Create an agent with database query capabilities."""
    demo = MCPToolDemo()

    # Search for database tools
    results = demo.search_tools("database")

    if results:

        # Filter for Python database tools with high stars
        python_db_tools = [
            s for s in results if s.get("language", "").lower() == "python"
        ]

        if python_db_tools:
            for _i, server in enumerate(python_db_tools[:3], 1):
                pass

            # Create multiple tools
            tools = []
            for server in python_db_tools[:2]:  # Use top 2
                tool = demo.create_mcp_tool_wrapper(server)
                tools.append(tool)

            # Create ReactAgent with multiple tools
            agent = ReactAgent(
                name="database_agent",
                engine=AugLLMConfig(
                    temperature=0.5,
                    system_message="You are a database expert with access to various database tools.",
                ),
                tools=tools,
            )

            # Test the agent
            await agent.arun("Query the user table for active users")
    else:
        pass


async def demo_custom_tool_creation():
    """Demo: Create custom tool wrappers for MCP servers."""


async def show_fastmcp_integration():
    """Show FastMCP server integration."""


async def main():
    """Run all demos."""
    # Check if data exists
    demo = MCPToolDemo()
    if not demo.servers_data:
        return

    # Run demos
    await demo_calculator_agent()
    await demo_database_agent()
    await demo_custom_tool_creation()
    await show_fastmcp_integration()


if __name__ == "__main__":
    asyncio.run(main())
