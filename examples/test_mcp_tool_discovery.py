#!/usr/bin/env python3
"""Test MCP Tool Discovery and Agent Integration.

This example shows:
1. How to search for MCP tools
2. How to integrate them with haive agents
3. Practical usage patterns
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "haive" / "mcp"))

from integrated_mcp_system import IntegratedMCPSystem
from self_query_mcp_agent import SelfQueryMCPAgent


async def test_tool_discovery():
    """Test discovering MCP tools by various queries."""
    # Initialize the discovery system
    system = IntegratedMCPSystem()

    # Test queries
    test_queries = [
        "calculator tool",
        "Python database tools with high stars",
        "web scraping tools",
        "file system tools",
        "API tools with more than 5 stars",
    ]

    for query in test_queries:

        results = await system.search_servers(query, method="auto")

        if results["documents"]:

            for _i, doc in enumerate(results["documents"][:3], 1):

                # Show description snippet
                content = doc.page_content
                desc_start = content.find("Description")
                if desc_start > -1:
                    desc_end = content.find("\n\n", desc_start)
                    desc = content[desc_start:desc_end].replace("Description\n", "")
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
        else:
            pass


async def test_specific_tool_search():
    """Test searching for specific types of tools."""
    agent = SelfQueryMCPAgent()

    # Test self-query for structured searches
    structured_queries = [
        "database servers in Python with more than 10 stars",
        "web servers with tools and resources",
        "file system tools with installation commands",
    ]

    for query in structured_queries:

        try:
            docs = await agent.search_with_self_query(query, k=3)

            if docs:
                for _i, _doc in enumerate(docs, 1):
                    pass
            else:
                pass

        except Exception:
            pass


async def show_integration_example():
    """Show how to integrate discovered tools with haive agents."""


async def main():
    """Run all tests."""
    # Test basic discovery
    await test_tool_discovery()

    # Test specific searches
    await test_specific_tool_search()

    # Show integration example
    await show_integration_example()


if __name__ == "__main__":
    asyncio.run(main())
