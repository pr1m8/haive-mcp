"""Test MCP RAG Agent directly without server"""

import asyncio
from pathlib import Path
import sys


# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_simple_rag_agent import create_mcp_rag_agent


async def test_direct():
    """Test the RAG agent directly."""
    print("🚀 Creating MCP RAG agent...")
    agent = create_mcp_rag_agent()

    # Test queries
    queries = [
        "python database",
        "What Python MCP servers can help with databases?",
        "github integration",
        "file system operations",
    ]

    for query in queries:
        print(f"\n{'=' * 60}")
        print(f"🔍 Query: {query}")
        print(f"{'=' * 60}")

        try:
            # Run with debug mode
            result = await agent.arun(query, debug=True)

            print(f"\n📊 Result type: {type(result)}")
            print(f"📊 Result: {result}")

            if hasattr(result, "__dict__"):
                print(f"📊 Result attributes: {result.__dict__}")

            if hasattr(result, "retrieved_documents"):
                docs = result.retrieved_documents
                print(f"\n📚 Retrieved {len(docs)} documents")

                if docs:
                    for i, doc in enumerate(docs[:3], 1):
                        print(f"\n{i}. {doc.metadata.get('server_name', 'Unknown')}")
                        print(f"   Category: {doc.metadata.get('category', 'unknown')}")
                        print(f"   Stars: {doc.metadata.get('stars', 0)}")
                else:
                    # Try direct vector store access
                    print("\n⚠️ No documents retrieved. Trying direct vector store...")

                    # Access the vector store directly
                    if hasattr(agent, "engine") and hasattr(
                        agent.engine, "create_vectorstore"
                    ):
                        vectorstore = agent.engine.create_vectorstore()
                        direct_results = vectorstore.similarity_search(query, k=5)

                        print(f"\n🔍 Direct search found {len(direct_results)} results")
                        for i, doc in enumerate(direct_results[:3], 1):
                            print(
                                f"\n{i}. {doc.metadata.get('server_name', 'Unknown')}"
                            )
                            print(
                                f"   Category: {doc.metadata.get('category', 'unknown')}"
                            )
                            print(f"   Stars: {doc.metadata.get('stars', 0)}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()

        await asyncio.sleep(1)  # Small delay between queries


if __name__ == "__main__":
    print("🧪 Testing MCP RAG Agent directly...")
    asyncio.run(test_direct())
