"""
Simple test for MCP RAG Agent without circular imports
"""
import os
import sys

# Set the PYTHONPATH to the haive backend
backend_path = "/home/will/Projects/haive/backend/haive"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Now import
from packages.haive_mcp.src.haive.mcp.mcp_simple_rag_agent import create_mcp_rag_agent
import asyncio

async def test():
    print("Creating MCP RAG agent...")
    agent = create_mcp_rag_agent()
    
    print("\nTesting query: 'python database'")
    result = await agent.arun("python database")
    
    print(f"\nResult type: {type(result)}")
    if hasattr(result, 'retrieved_documents'):
        docs = result.retrieved_documents
        print(f"Retrieved {len(docs)} documents")
        
        if docs:
            for i, doc in enumerate(docs[:3], 1):
                print(f"\n{i}. {doc.metadata.get('server_name', 'Unknown')}")
                print(f"   Category: {doc.metadata.get('category', 'unknown')}")
    else:
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())