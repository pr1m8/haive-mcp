"""Simple test for MCP RAG Agent without circular imports."""

import sys

# Set the PYTHONPATH to the haive backend
backend_path = "/home/will/Projects/haive/backend/haive"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now import
import asyncio

from packages.haive_mcp.src.haive.mcp.mcp_simple_rag_agent import create_mcp_rag_agent


async def test():
    agent = create_mcp_rag_agent()

    result = await agent.arun("python database")

    if hasattr(result, "retrieved_documents"):
        docs = result.retrieved_documents

        if docs:
            for _i, _doc in enumerate(docs[:3], 1):
                pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(test())
