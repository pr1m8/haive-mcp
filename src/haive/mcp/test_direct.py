"""Test MCP RAG Agent directly without server."""

import asyncio

from haive.mcp.mcp_simple_rag_agent import create_mcp_rag_agent


async def test_direct():
    """Test the RAG agent directly."""
    agent = create_mcp_rag_agent()

    # Test queries
    queries = [
        "python database",
        "What Python MCP servers can help with databases?",
        "github integration",
        "file system operations",
    ]

    for query in queries:

        try:
            # Run with debug mode
            result = await agent.arun(query, debug=True)

            # The result is a RetrieverOutput object
            if hasattr(result, "retrieved_documents"):
                docs = result.retrieved_documents
            else:
                if hasattr(result, "__dict__"):
                    pass
                docs = []

            if docs:
                for _i, _doc in enumerate(docs[:3], 1):
                    pass
            # Try direct vector store access

            # Access the vector store directly
            elif hasattr(agent, "engine") and hasattr(
                agent.engine, "create_vectorstore"
            ):
                vectorstore = agent.engine.create_vectorstore()
                direct_results = vectorstore.similarity_search(query, k=5)

                for _i, _doc in enumerate(direct_results[:3], 1):
                    pass

        except Exception:
            import traceback

            traceback.print_exc()

        await asyncio.sleep(1)  # Small delay between queries


if __name__ == "__main__":
    asyncio.run(test_direct())
