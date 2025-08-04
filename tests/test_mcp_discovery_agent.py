#!/usr/bin/env python3
"""Test MCP Discovery to Agent Integration.

This example demonstrates:
1. Searching for MCP tools by query
2. Creating haive agents with discovered tools
3. Using the agents to perform tasks
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Standard haive imports - no special path manipulation needed
try:
    from haive.agents.react import ReactAgent
    from haive.agents.simple import SimpleAgent
    from haive.core.engine.aug_llm import AugLLMConfig
    from langchain_core.tools import Tool

except ImportError:
    sys.exit(1)


class SimpleMCPDiscovery:
    """Simple MCP discovery without external dependencies."""

    def __init__(self):
        # Find the MCP data file
        current_dir = Path(__file__).parent
        data_locations = [
            current_dir.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json",
            current_dir.parent.parent.parent.parent
            / "data"
            / "mcp_servers"
            / "ALL_MCP_SERVERS_COMPLETE.json",
            Path(
                "/home/will/Projects/haive/backend/haive/data/mcp_servers/ALL_MCP_SERVERS_COMPLETE.json"
            ),
        ]

        self.data_path = None
        for path in data_locations:
            if path.exists():
                self.data_path = path
                break

        if not self.data_path:
            for path in data_locations:
                pass

        self.servers_data = []

    def load_data(self) -> bool:
        """Load MCP servers data."""
        if not self.data_path:
            return False

        try:
            with open(self.data_path) as f:
                data = json.load(f)
                self.servers_data = data.get("all_servers", [])
                return True
        except Exception:
            return False

    def search_tools(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Simple search for MCP tools."""
        if not self.servers_data and not self.load_data():
            return []

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

        # Sort by stars (handle None values)
        results.sort(key=lambda x: x.get("stars", 0) or 0, reverse=True)

        return results[:max_results]


def create_mock_mcp_tool(server_info: dict[str, Any]) -> Tool:
    """Create a mock tool for an MCP server."""
    server_name = server_info.get("name", "unknown")
    description = server_info.get("description", "MCP tool")
    tools_list = server_info.get("tools", [])

    # Create a more realistic mock based on the server type
    def tool_function(input: str) -> str:
        """Mock MCP tool execution."""
        # Different responses based on server type
        if "calculator" in server_name.lower():
            return f"Calculation result: [simulated calculation of '{input}']"
        if "database" in server_name.lower() or "sql" in server_name.lower():
            return (
                f"Database query result: [simulated query '{input}' - returned 10 rows]"
            )
        if "web" in server_name.lower() or "scraper" in server_name.lower():
            return f"Web scraping result: [scraped content from '{input}' - 500 words extracted]"
        if "file" in server_name.lower():
            return f"File operation result: [performed operation on '{input}']"
        return f"[MCP Tool '{server_name}'] Processed: {input}"

    # Clean name for tool
    tool_name = (
        server_name.replace("-", "_")
        .replace(" ", "_")
        .replace("@", "")
        .replace("/", "_")
    )

    return Tool(
        name=tool_name[:50],  # Limit name length
        description=f"{description[:100]}. Available operations: {', '.join(tools_list[:3]) if tools_list else 'general'}",
        func=tool_function,
    )


async def demo_calculator_agent():
    """Demo: Create an agent with calculator capabilities."""
    discovery = SimpleMCPDiscovery()

    # Search for calculator tools
    results = discovery.search_tools("calculator")

    if not results:
        return

    for _i, _server in enumerate(results[:3], 1):
        pass

    # Use the first calculator tool
    selected = results[0]

    # Create tool wrapper
    calc_tool = create_mock_mcp_tool(selected)

    # Create agent with the tool
    try:
        config = AugLLMConfig(
            temperature=0.7,
            system_message="You are a helpful assistant with access to a calculator tool. Use it when asked to perform calculations.",
        )

        SimpleAgent(name="calculator_agent", engine=config, tools=[calc_tool])

        # Test queries
        test_queries = [
            "What is 42 * 17?",
            "Calculate the sum of 123 and 456",
            "What's 1000 divided by 25?",
        ]

        for query in test_queries:
            try:
                # Note: In a real scenario, you'd use await agent.arun(query)
                # For this demo, we'll simulate the response
                calc_tool.func(query)
            except Exception:
                pass

    except Exception:
        pass


async def demo_database_agent():
    """Demo: Create an agent with database capabilities."""
    discovery = SimpleMCPDiscovery()

    # Search for database tools
    results = discovery.search_tools("database")

    if not results:
        # Try alternative search
        results = discovery.search_tools("sql")

    if not results:
        return

    # Filter for Python database tools
    python_db_tools = [
        s
        for s in results
        if s.get("language", "").lower() in ["python", "typescript", "javascript"]
    ]

    if not python_db_tools:
        python_db_tools = results  # Use all if no Python-specific found

    for _i, server in enumerate(python_db_tools[:3], 1):
        pass

    # Create multiple database tools
    tools = []
    for server in python_db_tools[:2]:  # Use top 2
        tool = create_mock_mcp_tool(server)
        tools.append(tool)

    # Create ReactAgent with multiple tools
    try:
        config = AugLLMConfig(
            temperature=0.5,
            system_message="You are a database expert with access to various database tools. Use them to answer queries about data.",
        )

        ReactAgent(name="database_agent", engine=config, tools=tools)

        # Test the agent
        test_queries = [
            "Query the user table for active users",
            "Show me the total sales from last month",
            "Find all customers from New York",
        ]

        for query in test_queries:
            try:
                # Simulate agent reasoning
                # In real usage: result = await agent.arun(query)
                tools[0].func(query)
            except Exception:
                pass

    except Exception:
        pass


async def demo_web_scraping_agent():
    """Demo: Create an agent with web scraping capabilities."""
    discovery = SimpleMCPDiscovery()

    # Search for web scraping tools
    results = discovery.search_tools("web scraping")

    if not results:
        results = discovery.search_tools("web")

    if not results:
        return

    for _i, _server in enumerate(results[:3], 1):
        pass

    # Create web scraping tool
    selected = results[0]
    create_mock_mcp_tool(selected)

    # Show how it would be used


async def show_discovery_stats():
    """Show statistics about available MCP tools."""
    discovery = SimpleMCPDiscovery()
    if not discovery.load_data():
        return

    # Categorize servers
    categories = {}
    languages = {}
    tool_counts = {"with_tools": 0, "without_tools": 0}

    for server in discovery.servers_data:
        # Category stats
        cat = server.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

        # Language stats
        lang = server.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

        # Tool stats
        if server.get("tools"):
            tool_counts["with_tools"] += 1
        else:
            tool_counts["without_tools"] += 1

    for cat, _count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        pass

    for lang, _count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[
        :10
    ]:
        pass


async def main():
    """Run all demos."""
    # Check if we can access MCP data
    discovery = SimpleMCPDiscovery()
    if not discovery.data_path:
        return

    # Show discovery statistics
    await show_discovery_stats()

    # Run demos
    await demo_calculator_agent()
    await demo_database_agent()
    await demo_web_scraping_agent()


if __name__ == "__main__":
    # Run with: poetry run python test_mcp_discovery_agent.py
    asyncio.run(main())
