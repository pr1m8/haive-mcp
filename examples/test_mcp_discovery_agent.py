#!/usr/bin/env python3
"""Test MCP Discovery to Agent Integration

This example demonstrates:
1. Searching for MCP tools by query
2. Creating haive agents with discovered tools
3. Using the agents to perform tasks
"""

import asyncio
import json
from pathlib import Path
from typing import Any

# Standard haive imports - no special path manipulation needed
try:
    from haive.agents.react import ReactAgent
    from haive.agents.simple import SimpleAgent
    from haive.core.engine.aug_llm import AugLLMConfig
    from langchain_core.tools import Tool

    print("✅ Haive imports successful")
except ImportError as e:
    print(f"❌ Error importing haive components: {e}")
    print("Make sure to run with: poetry run python test_mcp_discovery_agent.py")
    exit(1)


class SimpleMCPDiscovery:
    """Simple MCP discovery without external dependencies"""

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
            print("❌ Could not find MCP data file. Searched in:")
            for path in data_locations:
                print(f"   - {path}")

        self.servers_data = []

    def load_data(self) -> bool:
        """Load MCP servers data"""
        if not self.data_path:
            return False

        try:
            with open(self.data_path) as f:
                data = json.load(f)
                self.servers_data = data.get("all_servers", [])
                print(
                    f"✅ Loaded {len(self.servers_data)} MCP servers from {self.data_path}"
                )
                return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def search_tools(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Simple search for MCP tools"""
        if not self.servers_data:
            if not self.load_data():
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
    """Create a mock tool for an MCP server"""
    server_name = server_info.get("name", "unknown")
    description = server_info.get("description", "MCP tool")
    tools_list = server_info.get("tools", [])

    # Create a more realistic mock based on the server type
    def tool_function(input: str) -> str:
        """Mock MCP tool execution"""
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
    """Demo: Create an agent with calculator capabilities"""
    print("\n" + "=" * 60)
    print("📊 Demo 1: Simple Agent with Calculator Tool")
    print("=" * 60)

    discovery = SimpleMCPDiscovery()

    # Search for calculator tools
    print("\n🔍 Searching for calculator tools...")
    results = discovery.search_tools("calculator")

    if not results:
        print("❌ No calculator tools found")
        return

    print(f"✅ Found {len(results)} calculator tools:")
    for i, server in enumerate(results[:3], 1):
        print(f"\n{i}. {server.get('name', 'Unknown')}")
        print(f"   Stars: {server.get('stars', 0) or 'N/A'} ⭐")
        print(f"   Language: {server.get('language', 'unknown')}")
        print(f"   Tools: {', '.join(server.get('tools', [])[:3]) or 'N/A'}")

    # Use the first calculator tool
    selected = results[0]
    print(f"\n🎯 Using: {selected.get('name')}")

    # Create tool wrapper
    calc_tool = create_mock_mcp_tool(selected)
    print(f"✅ Created tool wrapper: {calc_tool.name}")

    # Create agent with the tool
    try:
        config = AugLLMConfig(
            temperature=0.7,
            system_message="You are a helpful assistant with access to a calculator tool. Use it when asked to perform calculations.",
        )

        SimpleAgent(name="calculator_agent", engine=config, tools=[calc_tool])

        print("\n🤖 Testing agent with calculator tool:")

        # Test queries
        test_queries = [
            "What is 42 * 17?",
            "Calculate the sum of 123 and 456",
            "What's 1000 divided by 25?",
        ]

        for query in test_queries:
            print(f"\n💬 User: {query}")
            try:
                # Note: In a real scenario, you'd use await agent.arun(query)
                # For this demo, we'll simulate the response
                print("🤖 Agent: I'll help you with that calculation.")
                print(f"   Using tool: {calc_tool.name}")
                tool_result = calc_tool.func(query)
                print(f"   Tool result: {tool_result}")
            except Exception as e:
                print(f"❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error creating agent: {e}")


async def demo_database_agent():
    """Demo: Create an agent with database capabilities"""
    print("\n" + "=" * 60)
    print("🗄️ Demo 2: React Agent with Database Tools")
    print("=" * 60)

    discovery = SimpleMCPDiscovery()

    # Search for database tools
    print("\n🔍 Searching for database tools...")
    results = discovery.search_tools("database")

    if not results:
        # Try alternative search
        results = discovery.search_tools("sql")

    if not results:
        print("❌ No database tools found")
        return

    print(f"✅ Found {len(results)} database tools:")

    # Filter for Python database tools
    python_db_tools = [
        s
        for s in results
        if s.get("language", "").lower() in ["python", "typescript", "javascript"]
    ]

    if not python_db_tools:
        python_db_tools = results  # Use all if no Python-specific found

    for i, server in enumerate(python_db_tools[:3], 1):
        print(f"\n{i}. {server.get('name', 'Unknown')}")
        print(f"   Language: {server.get('language', 'unknown')}")
        print(f"   Stars: {server.get('stars', 0) or 'N/A'} ⭐")
        print(f"   Category: {server.get('category', 'unknown')}")

    # Create multiple database tools
    tools = []
    for server in python_db_tools[:2]:  # Use top 2
        tool = create_mock_mcp_tool(server)
        tools.append(tool)
        print(f"\n✅ Created tool: {tool.name}")

    # Create ReactAgent with multiple tools
    try:
        config = AugLLMConfig(
            temperature=0.5,
            system_message="You are a database expert with access to various database tools. Use them to answer queries about data.",
        )

        ReactAgent(name="database_agent", engine=config, tools=tools)

        print(f"\n🤖 Created ReactAgent with {len(tools)} database tools")

        # Test the agent
        test_queries = [
            "Query the user table for active users",
            "Show me the total sales from last month",
            "Find all customers from New York",
        ]

        for query in test_queries:
            print(f"\n💬 User: {query}")
            try:
                # Simulate agent reasoning
                print("🤖 Agent: I'll help you with that database query.")
                print(f"   Available tools: {', '.join([t.name for t in tools])}")
                # In real usage: result = await agent.arun(query)
                tool_result = tools[0].func(query)
                print(f"   Tool result: {tool_result}")
            except Exception as e:
                print(f"❌ Error: {e}")

    except Exception as e:
        print(f"❌ Error creating agent: {e}")


async def demo_web_scraping_agent():
    """Demo: Create an agent with web scraping capabilities"""
    print("\n" + "=" * 60)
    print("🌐 Demo 3: Agent with Web Scraping Tools")
    print("=" * 60)

    discovery = SimpleMCPDiscovery()

    # Search for web scraping tools
    print("\n🔍 Searching for web scraping tools...")
    results = discovery.search_tools("web scraping")

    if not results:
        results = discovery.search_tools("web")

    if not results:
        print("❌ No web scraping tools found")
        return

    print(f"✅ Found {len(results)} web-related tools:")
    for i, server in enumerate(results[:3], 1):
        print(f"\n{i}. {server.get('name', 'Unknown')}")
        print(f"   Category: {server.get('category', 'unknown')}")
        print(f"   Description: {server.get('description', 'N/A')[:60]}...")

    # Create web scraping tool
    selected = results[0]
    web_tool = create_mock_mcp_tool(selected)

    print(f"\n✅ Created web scraping tool: {web_tool.name}")

    # Show how it would be used
    print("\n📝 Example usage with agent:")
    print(
        """
# Create agent with web scraping tool
agent = ReactAgent(
    name="web_research_agent",
    engine=AugLLMConfig(
        system_message="You are a web research assistant with scraping capabilities."
    ),
    tools=[web_tool]
)

# Use the agent
result = await agent.arun("Scrape the latest news from https://example.com")
"""
    )


async def show_discovery_stats():
    """Show statistics about available MCP tools"""
    print("\n" + "=" * 60)
    print("📊 MCP Tool Discovery Statistics")
    print("=" * 60)

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

    print(f"\n📈 Total MCP Servers: {len(discovery.servers_data)}")

    print("\n📂 By Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cat}: {count}")

    print("\n💻 By Language:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {lang}: {count}")

    print("\n🔧 Tool Availability:")
    print(f"   With tools listed: {tool_counts['with_tools']}")
    print(f"   Without tools: {tool_counts['without_tools']}")


async def main():
    """Run all demos"""
    print("🚀 MCP Discovery to Haive Agent Integration Test")
    print("=" * 70)

    # Check if we can access MCP data
    discovery = SimpleMCPDiscovery()
    if not discovery.data_path:
        print("\n❌ Cannot proceed without MCP data file")
        return

    # Show discovery statistics
    await show_discovery_stats()

    # Run demos
    await demo_calculator_agent()
    await demo_database_agent()
    await demo_web_scraping_agent()

    print("\n\n✅ All demos complete!")
    print("\n📝 Next steps:")
    print("1. Install actual MCP servers using npm or pip")
    print("2. Create real tool wrappers that connect to MCP servers")
    print("3. Use the integrated launcher for full functionality:")
    print("   cd packages/haive-mcp")
    print("   poetry run python src/haive/mcp/integrated_launcher.py web")


if __name__ == "__main__":
    # Run with: poetry run python test_mcp_discovery_agent.py
    asyncio.run(main())
