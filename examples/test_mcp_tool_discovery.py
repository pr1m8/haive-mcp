#!/usr/bin/env python3
"""Test MCP Tool Discovery and Agent Integration

This example shows:
1. How to search for MCP tools
2. How to integrate them with haive agents
3. Practical usage patterns
"""

import asyncio
from pathlib import Path
import sys


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "haive" / "mcp"))

from integrated_mcp_system import IntegratedMCPSystem
from self_query_mcp_agent import SelfQueryMCPAgent


async def test_tool_discovery():
    """Test discovering MCP tools by various queries"""
    print("🔍 Testing MCP Tool Discovery")
    print("=" * 50)

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
        print(f"\n📋 Query: {query}")
        print("-" * 40)

        results = await system.search_servers(query, method="auto")

        if results["documents"]:
            print(f"Found {len(results['documents'])} tools (showing top 3):")

            for i, doc in enumerate(results["documents"][:3], 1):
                metadata = doc.metadata
                print(f"\n{i}. {metadata.get('server_name', 'Unknown')}")
                print(f"   Category: {metadata.get('category', 'unknown')}")
                print(f"   Language: {metadata.get('language', 'unknown')}")
                print(f"   Stars: {metadata.get('stars', 0)} ⭐")
                print(f"   Tools: {metadata.get('tools_count', 0)}")
                print(
                    f"   Install: {(metadata.get('has_install', False) and '✅ Available') or '❌ Manual'}"
                )

                # Show description snippet
                content = doc.page_content
                desc_start = content.find("Description")
                if desc_start > -1:
                    desc_end = content.find("\n\n", desc_start)
                    desc = content[desc_start:desc_end].replace("Description\n", "")
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    print(f"   Description: {desc}")
        else:
            print("No tools found")


async def test_specific_tool_search():
    """Test searching for specific types of tools"""
    print("\n\n🎯 Testing Specific Tool Categories")
    print("=" * 50)

    agent = SelfQueryMCPAgent()

    # Test self-query for structured searches
    structured_queries = [
        "database servers in Python with more than 10 stars",
        "web servers with tools and resources",
        "file system tools with installation commands",
    ]

    for query in structured_queries:
        print(f"\n📋 Self-Query: {query}")
        print("-" * 40)

        try:
            docs = await agent.search_with_self_query(query, k=3)

            if docs:
                print(f"Found {len(docs)} matching tools:")
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    print(f"\n{i}. {metadata.get('server_name', 'Unknown')}")
                    print(
                        f"   Matches: category={metadata.get('category')}, "
                        f"language={metadata.get('language')}, "
                        f"stars={metadata.get('stars')}"
                    )
            else:
                print("No matches found")

        except Exception as e:
            print(f"Error: {e}")


async def show_integration_example():
    """Show how to integrate discovered tools with haive agents"""
    print("\n\n🤖 Haive Agent Integration Example")
    print("=" * 50)

    print(
        """
# Example: Integrating a discovered MCP tool with a haive agent

from haive.agents.react import ReactAgent
from haive.core.engine.aug_llm import AugLLMConfig
from langchain_core.tools import Tool
import subprocess
import json

# 1. After discovering and installing an MCP tool (e.g., 'calculator-mcp')

# 2. Create a wrapper function for the MCP tool
async def call_mcp_tool(query: str) -> str:
    \"\"\"Call an MCP server tool via stdio\"\"\"
    
    # Start the MCP server process
    process = subprocess.Popen(
        ['python', '-m', 'calculator_mcp'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request (MCP protocol)
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "calculate",
            "arguments": {"expression": query}
        }
    }
    
    process.stdin.write(json.dumps(request) + '\\n')
    process.stdin.flush()
    
    # Read response
    response = process.stdout.readline()
    result = json.loads(response)
    
    # Clean up
    process.terminate()
    
    return result.get('result', 'No result')

# 3. Create LangChain tool wrapper
calculator_tool = Tool(
    name="calculator",
    description="Calculate mathematical expressions",
    func=lambda x: asyncio.run(call_mcp_tool(x))
)

# 4. Create haive agent with the tool
agent = ReactAgent(
    name="math_assistant",
    engine=AugLLMConfig(
        system_message="You are a helpful math assistant with access to a calculator."
    ),
    tools=[calculator_tool]
)

# 5. Use the agent
result = await agent.arun("What is 25 * 4 + 10?")
print(f"Agent result: {result}")
    """
    )


async def main():
    """Run all tests"""
    print("🚀 MCP Tool Discovery and Integration Test")
    print("=" * 70)

    # Test basic discovery
    await test_tool_discovery()

    # Test specific searches
    await test_specific_tool_search()

    # Show integration example
    await show_integration_example()

    print("\n\n✅ Test complete!")
    print("\nTo use the full system:")
    print("1. Run: python integrated_launcher.py web")
    print("2. Search for tools")
    print("3. Install with one click")
    print("4. Use in your haive agents!")


if __name__ == "__main__":
    asyncio.run(main())
