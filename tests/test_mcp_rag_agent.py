"""Test MCP RAG Agent."""

import pytest
from haive.mcp.mcp_simple_rag_agent import create_mcp_rag_agent


@pytest.mark.asyncio
async def test_mcp_rag_agent():
    """Test the MCP RAG agent with documents."""
    # Create agent
    agent = create_mcp_rag_agent()
    
    # Test query
    result = await agent.arun("python database")
    
    # Check result
    assert result is not None
    
    # Should have retrieved_documents attribute
    assert hasattr(result, 'retrieved_documents')
    
    docs = result.retrieved_documents
    print(f"\nRetrieved {len(docs)} documents")
    
    # Print first few results
    for i, doc in enumerate(docs[:3], 1):
        server_name = doc.metadata.get('server_name', 'Unknown')
        category = doc.metadata.get('category', 'unknown')
        print(f"{i}. {server_name} ({category})")