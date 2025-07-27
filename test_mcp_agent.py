#!/usr/bin/env python3
"""Test MCP RAG agent without server."""

import asyncio
import sys
from pathlib import Path

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, "/home/will/Projects/haive/backend/haive/packages")

from src.haive.mcp.mcp_simple_rag_agent import create_mcp_rag_agent


async def test_agent():
    """Test the MCP agent with some queries."""
    print("🚀 Creating MCP RAG Agent...")

    try:
        # Create agent
        agent = create_mcp_rag_agent()
        print("✅ Agent created successfully!")

        # Test queries
        test_queries = [
            "database",
            "python",
            "postgresql",
            "file system",
            "github",
            "aws",
        ]

        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                result = await agent.arun(query)
                print(f"✅ Got result type: {type(result)}")
                print(f"📝 Result: {str(result)[:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback

                traceback.print_exc()

    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent())
